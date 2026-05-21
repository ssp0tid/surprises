#!/usr/bin/env node

import { Command } from "commander";
import { createPublishCommand } from "./commands/publish.js";
import { createSubscribeCommand } from "./commands/subscribe.js";
import { createListenCommand } from "./commands/listen.js";
import { createReplayCommand } from "./commands/replay.js";
import { createSchemaCommand } from "./commands/schema.js";
import { createServerCommand } from "./commands/server.js";

const program = new Command();

program
  .name("eventbus")
  .description(
    "A CLI tool for local event-driven architecture acting as a pub/sub message broker",
  )
  .version("1.0.0");

program.addCommand(createPublishCommand());
program.addCommand(createSubscribeCommand());
program.addCommand(createListenCommand());
program.addCommand(createReplayCommand());
program.addCommand(createSchemaCommand());
program.addCommand(createServerCommand());

program.parse();
