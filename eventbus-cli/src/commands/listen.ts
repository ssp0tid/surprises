import { Command } from "commander";
import chalk from "chalk";

export function createListenCommand(): Command {
  const command = new Command("listen");

  command
    .description("Listen to events via SSE (connects to running server)")
    .argument("<channel>", "Channel pattern to listen to")
    .option("-p, --port <port>", "Server port", "8080")
    .option("--host <host>", "Server host", "localhost")
    .option("-t, --token <token>", "Authentication token")
    .option("--json", "Output as JSON")
    .action(
      async (
        channel: string,
        options: {
          port?: string;
          host?: string;
          token?: string;
          json?: boolean;
        },
      ) => {
        const url = `http://${options.host}:${options.port}/events?channel=${encodeURIComponent(channel)}`;
        const headers: Record<string, string> = {};

        if (options.token) {
          headers["Authorization"] = `Bearer ${options.token}`;
        }

        console.log(chalk.blue(`Connecting to ${url}...`));

        try {
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

          console.log(chalk.green("Connected! Listening for events...\n"));

          process.on("SIGINT", () => {
            reader.cancel();
            process.exit(0);
          });

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
                      `[${event.timestamp}] ${chalk.cyan(event.type)}: ${JSON.stringify(event.payload)}`,
                    );
                  } catch {
                    console.log(data);
                  }
                }
              }
            }
          }
        } catch (err) {
          console.error(chalk.red("Connection error:"), err);
          process.exit(1);
        }
      },
    );

  return command;
}
