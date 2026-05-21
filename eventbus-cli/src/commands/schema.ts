import { Command } from "commander";
import { readFileSync } from "fs";
import { Storage } from "../lib/storage.js";
import { SchemaRegistry } from "../lib/schema-registry.js";
import { loadConfig } from "../utils/config.js";
import { EventbusError, SchemaValidationError } from "../lib/errors.js";
import chalk from "chalk";

export function createSchemaCommand(): Command {
  const command = new Command("schema");

  command
    .description("Manage event schemas")
    .argument("<command>", "Command: add, list, get, validate")
    .argument("[args...]", "Arguments for the command")
    .action(async (cmd: string, args: string[]) => {
      const config = loadConfig();
      const storage = new Storage({ path: config.storage.path });
      const registry = new SchemaRegistry(storage);

      try {
        switch (cmd) {
          case "add":
            await handleAdd(args, registry);
            break;
          case "list":
            handleList(registry);
            break;
          case "get":
            handleGet(args, registry);
            break;
          case "validate":
            handleValidate(args, registry);
            break;
          default:
            console.error(chalk.red(`Unknown command: ${cmd}`));
            command.help();
        }
      } catch (err) {
        if (err instanceof EventbusError) {
          console.error(chalk.red(`Error: ${err.message}`));
          process.exit(1);
        }
        console.error(chalk.red("Error:"), err);
        process.exit(1);
      } finally {
        storage.close();
      }
    });

  return command;
}

async function handleAdd(
  args: string[],
  registry: SchemaRegistry,
): Promise<void> {
  if (args.length < 2) {
    console.error(
      chalk.red(
        "Usage: eventbus schema add <event-type> <version> [--schema <schema>] [--file <file>]",
      ),
    );
    process.exit(1);
  }

  const eventType = args[0];
  const version = args[1];
  const schemaIndex = args.indexOf("--schema");
  const fileIndex = args.indexOf("--file");

  let schema: object;

  if (schemaIndex !== -1 && args[schemaIndex + 1]) {
    schema = JSON.parse(args[schemaIndex + 1]);
  } else if (fileIndex !== -1 && args[fileIndex + 1]) {
    const fileContent = readFileSync(args[fileIndex + 1], "utf-8");
    schema = JSON.parse(fileContent);
  } else {
    console.error(chalk.red("Error: Provide --schema or --file"));
    process.exit(1);
  }

  registry.register(eventType, version, schema);
  console.log(chalk.green(`Schema registered for ${eventType} (${version})`));
}

function handleList(registry: SchemaRegistry): void {
  const schemas = registry.list();

  if (schemas.length === 0) {
    console.log(chalk.yellow("No schemas registered."));
    return;
  }

  console.log(chalk.blue("Registered schemas:\n"));
  for (const s of schemas) {
    console.log(`  ${chalk.cyan(s.eventType)} (${s.version})`);
    console.log(`    Created: ${s.createdAt}`);
    console.log(`    Schema: ${JSON.stringify(s.schema).substring(0, 50)}...`);
    console.log();
  }
}

function handleGet(args: string[], registry: SchemaRegistry): void {
  if (args.length < 1) {
    console.error(
      chalk.red("Usage: eventbus schema get <event-type> [version]"),
    );
    process.exit(1);
  }

  const eventType = args[0];
  const version = args[1] || "v1";
  const schema = registry.get(eventType, version);

  if (!schema) {
    console.error(chalk.red(`Schema not found: ${eventType} (${version})`));
    process.exit(1);
  }

  console.log(chalk.blue(`Schema for ${eventType} (${version}):\n`));
  console.log(JSON.stringify(schema.schema, null, 2));
}

function handleValidate(args: string[], registry: SchemaRegistry): void {
  if (args.length < 1) {
    console.error(
      chalk.red("Usage: eventbus schema validate <event-type> --data <json>"),
    );
    process.exit(1);
  }

  const eventType = args[0];
  const dataIndex = args.indexOf("--data");

  if (dataIndex === -1 || !args[dataIndex + 1]) {
    console.error(chalk.red("Error: Provide --data <json>"));
    process.exit(1);
  }

  const data = JSON.parse(args[dataIndex + 1]);

  try {
    registry.validate(data, eventType);
    console.log(chalk.green("Validation passed!"));
  } catch (err) {
    if (err instanceof SchemaValidationError) {
      console.error(chalk.red(`Validation failed: ${err.message}`));
      console.error(JSON.stringify(err.errors, null, 2));
    } else if (err instanceof EventbusError) {
      console.error(chalk.red(`Validation failed: ${err.message}`));
    }
    process.exit(1);
  }
}
