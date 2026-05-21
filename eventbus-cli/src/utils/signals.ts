import type { Server } from "http";

type CleanupFn = () => void | Promise<void>;

const cleanupFns: CleanupFn[] = [];

export function registerCleanup(fn: CleanupFn): void {
  cleanupFns.push(fn);
}

export async function setupGracefulShutdown(server: Server): Promise<void> {
  const shutdown = async (signal: string) => {
    console.log(`\nReceived ${signal}. Shutting down gracefully...`);

    server.close(async () => {
      console.log("HTTP server closed.");
    });

    for (const fn of cleanupFns) {
      try {
        await fn();
      } catch (err) {
        console.error("Cleanup error:", err);
      }
    }

    process.exit(0);
  };

  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));
}

export function writePidFile(pidPath: string): void {
  const { writeFileSync, existsSync, mkdirSync } = require("fs");
  const { dirname } = require("path");

  const dir = dirname(pidPath);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  writeFileSync(pidPath, String(process.pid));
}

export function removePidFile(pidPath: string): void {
  try {
    const { unlinkSync } = require("fs");
    unlinkSync(pidPath);
  } catch {}
}

export function isPidRunning(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

export function readPidFile(pidPath: string): number | null {
  try {
    const { readFileSync } = require("fs");
    const pid = parseInt(readFileSync(pidPath, "utf-8"), 10);
    return isNaN(pid) ? null : pid;
  } catch {
    return null;
  }
}
