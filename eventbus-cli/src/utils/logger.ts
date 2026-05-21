import chalk from "chalk";

export type LogLevel = "debug" | "info" | "warn" | "error";

const levels: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

const currentLevel: LogLevel = (process.env.LOG_LEVEL as LogLevel) || "info";

function shouldLog(level: LogLevel): boolean {
  return levels[level] >= levels[currentLevel];
}

export function debug(message: string, ...args: unknown[]): void {
  if (shouldLog("debug")) {
    console.log(chalk.gray("[DEBUG]"), message, ...args);
  }
}

export function info(message: string, ...args: unknown[]): void {
  if (shouldLog("info")) {
    console.log(chalk.blue("[INFO]"), message, ...args);
  }
}

export function warn(message: string, ...args: unknown[]): void {
  if (shouldLog("warn")) {
    console.warn(chalk.yellow("[WARN]"), message, ...args);
  }
}

export function error(message: string, ...args: unknown[]): void {
  if (shouldLog("error")) {
    console.error(chalk.red("[ERROR]"), message, ...args);
  }
}

export function success(message: string, ...args: unknown[]): void {
  if (shouldLog("info")) {
    console.log(chalk.green("[OK]"), message, ...args);
  }
}
