import { Command } from "commander";
import { readFileSync } from "fs";
import { Storage } from "../lib/storage.js";
import { SchemaRegistry } from "../lib/schema-registry.js";
import { EventBroker } from "../lib/broker.js";
import { loadConfig } from "../utils/config.js";
import { EventbusError } from "../lib/errors.js";
import chalk from "chalk";

export function createPublishCommand(): Command {
  const command = new Command("publish");

  command
    .description("Publish an event to a channel")
    .argument("<channel>", "Channel name (supports wildcards like users.*)")
    .argument("<type>", "Event type (e.g., user.created)")
    .argument("[payload]", "Event payload as JSON string", "{}")
    .option("-m, --meta <metadata>", "Event metadata as JSON string")
    .option("-f, --file <file>", "Read payload from file")
    .option("-q, --quiet", "Quiet mode (no output)")
    .option("-d, --db <path>", "Database path")
    .action(
      async (
        channel: string,
        type: string,
        payloadStr: string,
        options: {
          meta?: string;
          file?: string;
          quiet?: boolean;
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

          let payload: object;
          if (options.file) {
            const fileContent = readFileSync(options.file, "utf-8");
            payload = JSON.parse(fileContent);
          } else {
            payload = JSON.parse(payloadStr);
          }

          let metadata: object | undefined;
          if (options.meta) {
            metadata = JSON.parse(options.meta);
          }

          const event = await broker.publish(channel, type, payload, metadata);

          if (!options.quiet) {
            console.log(chalk.green("Event published successfully!"));
            console.log(`  ID: ${event.id}`);
            console.log(`  Channel: ${event.channel}`);
            console.log(`  Type: ${event.type}`);
            console.log(`  Timestamp: ${event.timestamp}`);
          }

          storage.close();
          process.exit(0);
        } catch (err) {
          if (err instanceof EventbusError) {
            console.error(chalk.red(`Error: ${err.message}`));
            process.exit(1);
          }
          if (err instanceof SyntaxError) {
            console.error(chalk.red("Error: Invalid JSON payload"));
            process.exit(1);
          }
          console.error(chalk.red("Error:"), err);
          process.exit(1);
        }
      },
    );

  return command;
}
