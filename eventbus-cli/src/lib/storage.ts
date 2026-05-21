import Database from "better-sqlite3";
import { mkdir, existsSync } from "fs";
import { dirname as dirnameSync } from "path";
import { homedir } from "os";
import { join } from "path";
import type { Event } from "./event.js";

export interface StorageOptions {
  path?: string;
  wal?: boolean;
  busyTimeout?: number;
}

export interface ReplayOptions {
  from?: string;
  to?: string;
  limit?: number;
}

const DEFAULT_DB_PATH = join(homedir(), ".eventbus", "data.db");

export class Storage {
  private db: Database.Database;

  constructor(options: StorageOptions = {}) {
    const dbPath = options.path || DEFAULT_DB_PATH;
    this.db = this.initDatabase(dbPath, options);
  }

  private initDatabase(
    dbPath: string,
    options: StorageOptions,
  ): Database.Database {
    const dbDir = dirnameSync(dbPath);
    if (!existsSync(dbDir)) {
      mkdir(dbDir, { recursive: true } as any);
    }

    const db = new Database(dbPath);

    if (options.wal !== false) {
      db.pragma("journal_mode = WAL");
    }
    if (options.busyTimeout) {
      db.pragma(`busy_timeout = ${options.busyTimeout}`);
    }

    this.createTables(db);
    return db;
  }

  private createTables(db: Database.Database): void {
    db.exec(`
      CREATE TABLE IF NOT EXISTS events (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        channel     TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload    TEXT NOT NULL,
        metadata   TEXT,
        timestamp  TEXT NOT NULL DEFAULT (datetime('now')),
        version    TEXT NOT NULL DEFAULT 'v1'
      );

      CREATE INDEX IF NOT EXISTS idx_channel ON events(channel, timestamp);
      CREATE INDEX IF NOT EXISTS idx_type ON events(event_type, timestamp);
      CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);

      CREATE TABLE IF NOT EXISTS channels (
        name       TEXT PRIMARY KEY,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE TABLE IF NOT EXISTS schemas (
        event_type TEXT PRIMARY KEY,
        version    TEXT NOT NULL,
        schema      TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      );
    `);
  }

  insertEvent(event: Event): Event {
    const stmt = this.db.prepare(`
      INSERT INTO events (channel, event_type, payload, metadata, timestamp, version)
      VALUES (?, ?, ?, ?, ?, ?)
    `);

    const result = stmt.run(
      event.channel,
      event.type,
      JSON.stringify(event.payload),
      event.metadata ? JSON.stringify(event.metadata) : null,
      event.timestamp,
      event.version,
    );

    this.ensureChannelExists(event.channel);

    return {
      ...event,
      id: result.lastInsertRowid as number,
    };
  }

  private ensureChannelExists(channel: string): void {
    const stmt = this.db.prepare(
      "INSERT OR IGNORE INTO channels (name) VALUES (?)",
    );
    stmt.run(channel);
  }

  getEvents(channelPattern: string, options: ReplayOptions = {}): Event[] {
    let query = "SELECT * FROM events WHERE channel LIKE ?";
    const params: (string | number)[] = [channelPattern.replace("*", "%")];

    if (options.from) {
      query += " AND timestamp >= ?";
      params.push(options.from);
    }
    if (options.to) {
      query += " AND timestamp <= ?";
      params.push(options.to);
    }

    query += " ORDER BY timestamp DESC";

    if (options.limit) {
      query += " LIMIT ?";
      params.push(options.limit);
    }

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as {
      id: number;
      channel: string;
      event_type: string;
      payload: string;
      metadata: string | null;
      timestamp: string;
      version: string;
    }[];

    return rows.map((row) => ({
      id: row.id,
      channel: row.channel,
      type: row.event_type,
      payload: JSON.parse(row.payload),
      metadata: row.metadata ? JSON.parse(row.metadata) : undefined,
      timestamp: row.timestamp,
      version: row.version,
    }));
  }

  listChannels(): string[] {
    const stmt = this.db.prepare("SELECT name FROM channels ORDER BY name");
    const rows = stmt.all() as { name: string }[];
    return rows.map((row) => row.name);
  }

  close(): void {
    this.db.close();
  }
}
