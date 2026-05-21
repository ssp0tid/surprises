import { Command } from "commander";
import { Storage } from "../lib/storage.js";
import { SchemaRegistry } from "../lib/schema-registry.js";
import { EventBroker } from "../lib/broker.js";
import { loadConfig } from "../utils/config.js";
import { EventbusError } from "../lib/errors.js";
import chalk from "chalk";

export function createReplayCommand(): Command {
  const command = new Command("replay");

  command
    .description("Replay events from a channel")
    .argument("<channel>", "Channel to replay (supports wildcards)")
    .option("-f, --from <timestamp>", "From timestamp (ISO 8601)")
    .option("-t, --to <timestamp>", "To timestamp (ISO 8601)")
    .option("-l, --limit <limit>", "Limit number of events", "100")
    .option("--json", "Output as JSON lines")
    .option("-d, --db <path>", "Database path")
    .action(
      async (
        channel: string,
        options: {
          from?: string;
          to?: string;
          limit?: string;
          json?: boolean;
          db?: string;
        },
      ) => {
        try {
          const config = loadConfig();
          const storage = new Storage({
            path: options.db || config.storage.path,
          });
          const schemaRegistry = new SchemaRegistry(storage);
          const broker = new EventBroker(storage, schemaRegistry);

          const events = broker.getEvents(channel, {
            from: options.from,
            to: options.to,
            limit: parseInt(options.limit || "100", 10),
          });

          if (events.length === 0) {
            console.log(chalk.yellow("No events found."));
            storage.close();
            process.exit(0);
          }

          if (options.json) {
            for (const event of events) {
              console.log(JSON.stringify(event));
            }
          } else {
            console.log(chalk.blue(`Found ${events.length} event(s):\n`));
            for (const event of events) {
              console.log(`[${event.timestamp}] ${chalk.cyan(event.type)}`);
              console.log(`  Channel: ${event.channel}`);
              console.log(`  Payload: ${JSON.stringify(event.payload)}`);
              if (event.metadata) {
                console.log(`  Metadata: ${JSON.stringify(event.metadata)}`);
              }
              console.log();
            }
          }

          storage.close();
          process.exit(0);
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
