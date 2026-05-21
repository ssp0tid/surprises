import { Command } from "commander";
import { Storage } from "../lib/storage.js";
import { SchemaRegistry } from "../lib/schema-registry.js";
import { EventBroker } from "../lib/broker.js";
import { ChannelManager } from "../lib/channel.js";
import { loadConfig } from "../utils/config.js";
import { EventbusError } from "../lib/errors.js";
import chalk from "chalk";

export function createSubscribeCommand(): Command {
  const command = new Command("subscribe");

  command
    .description("Subscribe to events on a channel")
    .argument(
      "<channel-pattern>",
      "Channel pattern (supports wildcards like users.*)",
    )
    .option(
      "-f, --filter <filter>",
      'Content filter (e.g., "payload.amount > 100")',
    )
    .option("--once", "Receive only one event and exit")
    .option("--json", "Output as JSON lines")
    .option("-c, --count", "Count events only (no output)")
    .option("-d, --db <path>", "Database path")
    .option("--host <host>", "Server host (for remote mode)", "localhost")
    .option("--port <port>", "Server port (for remote mode)", "8080")
    .option("--token <token>", "API token (for remote mode)")
    .action(
      async (
        pattern: string,
        options: {
          filter?: string;
          once?: boolean;
          json?: boolean;
          count?: boolean;
          db?: string;
          host?: string;
          port?: string;
          token?: string;
        },
      ) => {
        try {
          if (options.host !== "localhost" || options.port !== "8080") {
            await subscribeRemote(pattern, options);
            return;
          }

          const config = loadConfig();
          const storage = new Storage({
            path: options.db || config.storage.path,
          });
          const schemaRegistry = new SchemaRegistry(storage);
          const broker = new EventBroker(storage, schemaRegistry);
          const channelManager = new ChannelManager();

          let filter;
          if (options.filter) {
            filter = channelManager.parseFilter(options.filter);
          }

          let count = 0;
          const displayEvent = (event: any) => {
            count++;
            if (options.count) {
              return;
            }
            if (options.json) {
              console.log(JSON.stringify(event));
            } else {
              console.log(
                `[${event.timestamp}] ${event.type}: ${JSON.stringify(event.payload)}`,
              );
            }
          };

          const subscription = broker.subscribe(pattern, displayEvent, filter);

          console.log(
            chalk.blue(`Subscribed to ${pattern}. Waiting for events...`),
          );

          if (options.once) {
            setTimeout(() => {
              broker.unsubscribe(subscription);
              storage.close();
              if (options.count) {
                console.log(count);
              }
              process.exit(0);
            }, 5000);
          }

          process.on("SIGINT", () => {
            broker.unsubscribe(subscription);
            storage.close();
            if (options.count) {
              console.log(count);
            }
            process.exit(0);
          });
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

async function subscribeRemote(pattern: string, options: any): Promise<void> {
  const url = `http://${options.host}:${options.port}/events?channel=${encodeURIComponent(pattern)}`;
  const headers: Record<string, string> = {};
  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  console.log(chalk.blue(`Connecting to ${url}...`));

  const response = await fetch(url, { headers });

  if (!response.ok) {
    console.error(
      chalk.red(`Error: ${response.status} ${response.statusText}`),
    );
    process.exit(1);
  }

  if (!response.body) {
    console.error(chalk.red("Error: No response body"));
    process.exit(1);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  console.log(chalk.blue(`Subscribed to ${pattern}. Waiting for events...`));

  process.on("SIGINT", () => {
    reader.cancel();
    process.exit(0);
  });

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.substring(6);
          if (options.json) {
            console.log(data);
          } else {
            try {
              const event = JSON.parse(data);
              console.log(
                `[${event.timestamp}] ${event.type}: ${JSON.stringify(event.payload)}`,
              );
            } catch {
              console.log(data);
            }
          }
        }
      }
    }
  } catch (err) {
    if ((err as Error).name !== "AbortError") {
      console.error(chalk.red("Error:"), err);
    }
  }
}
