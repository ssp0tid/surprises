import { Command } from "commander";
import http from "http";
import { Storage } from "../lib/storage.js";
import { SchemaRegistry } from "../lib/schema-registry.js";
import { EventBroker } from "../lib/broker.js";
import { loadConfig } from "../utils/config.js";
import {
  setupGracefulShutdown,
  registerCleanup,
  writePidFile,
  removePidFile,
  readPidFile,
  isPidRunning,
} from "../utils/signals.js";
import { EventbusError, errorToHttpStatus } from "../lib/errors.js";
import chalk from "chalk";

export function createServerCommand(): Command {
  const command = new Command("server");

  command
    .description("Start eventbus server (daemon mode)")
    .option("-d, --daemon", "Run as daemon in background")
    .option("-p, --port <port>", "Server port", "8080")
    .option("-h, --host <host>", "Server host", "localhost")
    .option("--db <path>", "Database path")
    .option("--api-key <key>", "API key for authentication")
    .option("--pid <path>", "PID file path")
    .option("--no-daemon", "Run in foreground (default)")
    .action(
      async (options: {
        daemon?: boolean;
        port?: string;
        host?: string;
        db?: string;
        apiKey?: string;
        pid?: string;
        noDaemon?: boolean;
      }) => {
        try {
          if (options.daemon) {
            await startDaemon(options);
            return;
          }

          await startServer(options);
        } catch (err) {
          if (err instanceof EventbusError) {
            console.error(chalk.red(`Error: ${err.message}`));
            process.exit(1);
          }
          console.error(chalk.red("Error:"), err);
          process.exit(1);
        }
      },
    );

  return command;
}

async function startDaemon(options: any): Promise<void> {
  const pidPath = options.pid || `${process.env.HOME}/.eventbus/eventbus.pid`;

  const existingPid = readPidFile(pidPath);
  if (existingPid && isPidRunning(existingPid)) {
    console.error(chalk.red(`Server already running with PID ${existingPid}`));
    process.exit(1);
  }

  const { spawn } = await import("child_process");
  const child = spawn(
    process.execPath,
    [
      __filename,
      "server",
      "-p",
      options.port,
      "-h",
      options.host,
      "--no-daemon",
    ],
    {
      detached: true,
      stdio: "ignore",
    },
  );

  child.unref();

  writePidFile(pidPath);
  console.log(chalk.green(`Server started with PID ${child.pid}`));
  process.exit(0);
}

async function startServer(options: any): Promise<void> {
  const config = loadConfig();
  const port = parseInt(options.port) || config.server.port;
  const host = options.host || config.server.host;

  const storage = new Storage({
    path: options.db || config.storage.path,
  });
  const schemaRegistry = new SchemaRegistry(storage);
  const broker = new EventBroker(storage, schemaRegistry);

  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url || "/", `http://${host}:${port}`);

      if (options.apiKey) {
        const auth = req.headers.authorization;
        if (!auth || auth !== `Bearer ${options.apiKey}`) {
          res.writeHead(401, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: "Unauthorized" }));
          return;
        }
      }

      if (url.pathname === "/events" && req.method === "GET") {
        await handleSSE(broker, req, res, url);
      } else if (url.pathname === "/publish" && req.method === "POST") {
        await handlePublish(broker, req, res);
      } else if (url.pathname === "/channels" && req.method === "GET") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ channels: broker.listChannels() }));
      } else if (url.pathname === "/schemas" && req.method === "GET") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ schemas: schemaRegistry.list() }));
      } else {
        res.writeHead(404, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Not found" }));
      }
    } catch (err) {
      const status =
        err instanceof EventbusError ? errorToHttpStatus[err.code] || 500 : 500;

      res.writeHead(status, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          error:
            err instanceof EventbusError
              ? err.message
              : "Internal server error",
        }),
      );
    }
  });

  await setupGracefulShutdown(server);
  registerCleanup(() => {
    storage.close();
    if (options.pid) {
      removePidFile(options.pid);
    }
  });

  server.listen(port, host, () => {
    console.log(
      chalk.green(`Eventbus server running at http://${host}:${port}`),
    );
    console.log(chalk.blue("Endpoints:"));
    console.log(`  GET  /events?channel=<pattern>  - SSE stream`);
    console.log(`  POST /publish              - Publish event`);
    console.log(`  GET  /channels            - List channels`);
    console.log(`  GET  /schemas            - List schemas`);
  });

  server.on("error", (err: NodeJS.ErrnoException) => {
    if (err.code === "EADDRINUSE") {
      console.error(chalk.red(`Port ${port} is already in use`));
      process.exit(1);
    }
    throw err;
  });
}

async function handleSSE(
  broker: EventBroker,
  req: http.IncomingMessage,
  res: http.ServerResponse,
  url: URL,
): Promise<void> {
  const channel = url.searchParams.get("channel") || "*";

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });

  res.write(": connected\n\n");

  const subscription = broker.subscribe(channel, (event) => {
    res.write(`event: ${event.type}\n`);
    res.write(`data: ${JSON.stringify(event)}\n\n`);
  });

  req.on("close", () => {
    broker.unsubscribe(subscription);
  });
}

async function handlePublish(
  broker: EventBroker,
  req: http.IncomingMessage,
  res: http.ServerResponse,
): Promise<void> {
  const chunks: Buffer[] = [];

  for await (const chunk of req) {
    chunks.push(chunk);
  }

  const body = JSON.parse(Buffer.concat(chunks).toString());
  const { channel, type, payload, metadata } = body;

  if (!channel || !type || !payload) {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        error: "Missing required fields: channel, type, payload",
      }),
    );
    return;
  }

  const event = await broker.publish(channel, type, payload, metadata);

  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify(event));
}
