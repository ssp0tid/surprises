import { homedir } from "os";
import { join } from "path";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";

export interface EventbusConfig {
  server: {
    host: string;
    port: number;
    apiKey: string | null;
  };
  storage: {
    path: string;
    wal: boolean;
    busyTimeout: number;
  };
  logging: {
    level: string;
    path: string;
  };
}

const DEFAULT_CONFIG: EventbusConfig = {
  server: {
    host: "localhost",
    port: 8080,
    apiKey: null,
  },
  storage: {
    path: join(homedir(), ".eventbus", "data.db"),
    wal: true,
    busyTimeout: 5000,
  },
  logging: {
    level: "info",
    path: join(homedir(), ".eventbus", "logs"),
  },
};

export function getConfigPath(): string {
  return join(homedir(), ".eventbus", "config.json");
}

export function loadConfig(): EventbusConfig {
  const configPath = getConfigPath();

  if (!existsSync(configPath)) {
    const configDir = join(homedir(), ".eventbus");
    if (!existsSync(configDir)) {
      mkdirSync(configDir, { recursive: true });
    }
    saveConfig(DEFAULT_CONFIG);
    return DEFAULT_CONFIG;
  }

  try {
    const data = readFileSync(configPath, "utf-8");
    return { ...DEFAULT_CONFIG, ...JSON.parse(data) };
  } catch {
    return DEFAULT_CONFIG;
  }
}

export function saveConfig(config: EventbusConfig): void {
  const configPath = getConfigPath();
  writeFileSync(configPath, JSON.stringify(config, null, 2));
}

export function updateConfig(updates: Partial<EventbusConfig>): EventbusConfig {
  const config = loadConfig();
  const newConfig = { ...config, ...updates };
  saveConfig(newConfig);
  return newConfig;
}
