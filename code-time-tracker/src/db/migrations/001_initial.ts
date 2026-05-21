import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export function runMigration(db: Database.Database): void {
  const schemaPath = path.join(__dirname, '..', 'schema.sql');
  const schema = fs.readFileSync(schemaPath, 'utf8');

  db.exec(schema);

  const insertDefaultSettings = db.prepare(`
    INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
  `);

  const defaults = [
    ['idle_threshold_seconds', '300'],
    ['poll_interval_ms', '5000'],
    ['max_session_duration_hours', '8'],
    ['auto_start', 'false'],
    ['theme', 'dark'],
    ['version', '1.0.0']
  ];

  const insertMany = db.transaction((settings: string[][]) => {
    for (const [key, value] of settings) {
      insertDefaultSettings.run(key, value);
    }
  });

  insertMany(defaults);
}