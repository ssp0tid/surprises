import Database from 'better-sqlite3';

export interface Project {
  id: string;
  name: string;
  color: string;
  keywords: string | null;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: number;
  project_id: string | null;
  start_time: string;
  end_time: string | null;
  duration_seconds: number | null;
  window_title: string | null;
  created_at: string;
}

export interface IdlePeriod {
  id: number;
  start_time: string;
  end_time: string;
  duration_seconds: number;
}

export interface Setting {
  key: string;
  value: string | null;
}

export interface ProjectInput {
  id: string;
  name: string;
  color?: string;
  keywords?: string[];
}

export interface SessionInput {
  project_id?: string;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  window_title?: string;
}

export interface SessionUpdate {
  end_time?: string;
  duration_seconds?: number;
}

export interface IdlePeriodInput {
  start_time: string;
  end_time: string;
  duration_seconds: number;
}

export class Repository {
  private db: Database.Database;

  constructor(db: Database.Database) {
    this.db = db;
  }

  transaction<T>(fn: () => T): T {
    return this.db.transaction(fn)();
  }

  projects = {
    insert(input: ProjectInput): Project {
      const stmt = this.db.prepare(`
        INSERT INTO projects (id, name, color, keywords)
        VALUES (?, ?, ?, ?)
      `);
      stmt.run(
        input.id,
        input.name,
        input.color ?? '#6366f1',
        input.keywords ? JSON.stringify(input.keywords) : null
      );
      return this.projects.findById(input.id)!;
    },

    findAll(): Project[] {
      const stmt = this.db.prepare(`
        SELECT * FROM projects ORDER BY created_at DESC
      `);
      return stmt.all() as Project[];
    },

    findById(id: string): Project | undefined {
      const stmt = this.db.prepare(`
        SELECT * FROM projects WHERE id = ?
      `);
      return stmt.get(id) as Project | undefined;
    },

    update(id: string, input: Partial<Omit<ProjectInput, 'id'>>): Project | undefined {
      const fields: string[] = [];
      const values: (string | null)[] = [];

      if (input.name !== undefined) {
        fields.push('name = ?');
        values.push(input.name);
      }
      if (input.color !== undefined) {
        fields.push('color = ?');
        values.push(input.color);
      }
      if (input.keywords !== undefined) {
        fields.push('keywords = ?');
        values.push(input.keywords ? JSON.stringify(input.keywords) : null);
      }

      if (fields.length === 0) {
        return this.projects.findById(id);
      }

      fields.push('updated_at = CURRENT_TIMESTAMP');
      values.push(id);

      const stmt = this.db.prepare(`
        UPDATE projects SET ${fields.join(', ')} WHERE id = ?
      `);
      stmt.run(...values);
      return this.projects.findById(id);
    },

    delete(id: string): boolean {
      const stmt = this.db.prepare(`
        DELETE FROM projects WHERE id = ?
      `);
      const result = stmt.run(id);
      return result.changes > 0;
    },

    merge(sourceId: string, targetId: string): boolean {
      const mergeTx = this.db.transaction(() => {
        const updateSessions = this.db.prepare(`
          UPDATE sessions SET project_id = ? WHERE project_id = ?
        `);
        updateSessions.run(targetId, sourceId);

        const deleteProject = this.db.prepare(`
          DELETE FROM projects WHERE id = ?
        `);
        deleteProject.run(sourceId);
      });

      try {
        mergeTx();
        return true;
      } catch {
        return false;
      }
    }
  };

  sessions = {
    insert(input: SessionInput): Session {
      const stmt = this.db.prepare(`
        INSERT INTO sessions (project_id, start_time, end_time, duration_seconds, window_title)
        VALUES (?, ?, ?, ?, ?)
      `);
      stmt.run(
        input.project_id ?? null,
        input.start_time,
        input.end_time ?? null,
        input.duration_seconds ?? null,
        input.window_title ?? null
      );
      const lastId = this.db.prepare('SELECT last_insert_rowid() as id').get() as { id: number };
      return this.sessions.findById(lastId.id)!;
    },

    findAll(filters?: {
      project_id?: string;
      from?: string;
      to?: string;
    }): Session[] {
      let query = 'SELECT * FROM sessions';
      const conditions: string[] = [];
      const params: (string | null)[] = [];

      if (filters?.project_id) {
        conditions.push('project_id = ?');
        params.push(filters.project_id);
      }
      if (filters?.from) {
        conditions.push('start_time >= ?');
        params.push(filters.from);
      }
      if (filters?.to) {
        conditions.push('start_time <= ?');
        params.push(filters.to);
      }

      if (conditions.length > 0) {
        query += ' WHERE ' + conditions.join(' AND ');
      }

      query += ' ORDER BY start_time DESC';

      const stmt = this.db.prepare(query);
      return stmt.all(...params) as Session[];
    },

    findById(id: number): Session | undefined {
      const stmt = this.db.prepare(`
        SELECT * FROM sessions WHERE id = ?
      `);
      return stmt.get(id) as Session | undefined;
    },

    update(id: number, input: SessionUpdate): Session | undefined {
      const fields: string[] = [];
      const values: (string | number | null)[] = [];

      if (input.end_time !== undefined) {
        fields.push('end_time = ?');
        values.push(input.end_time);
      }
      if (input.duration_seconds !== undefined) {
        fields.push('duration_seconds = ?');
        values.push(input.duration_seconds);
      }

      if (fields.length === 0) {
        return this.sessions.findById(id);
      }

      values.push(id);

      const stmt = this.db.prepare(`
        UPDATE sessions SET ${fields.join(', ')} WHERE id = ?
      `);
      stmt.run(...values);
      return this.sessions.findById(id);
    },

    delete(id: number): boolean {
      const stmt = this.db.prepare(`
        DELETE FROM sessions WHERE id = ?
      `);
      const result = stmt.run(id);
      return result.changes > 0;
    },

    findOrphans(): Session[] {
      const stmt = this.db.prepare(`
        SELECT * FROM sessions WHERE end_time IS NULL ORDER BY start_time DESC
      `);
      return stmt.all() as Session[];
    }
  };

  idlePeriods = {
    insert(input: IdlePeriodInput): IdlePeriod {
      const stmt = this.db.prepare(`
        INSERT INTO idle_periods (start_time, end_time, duration_seconds)
        VALUES (?, ?, ?)
      `);
      stmt.run(input.start_time, input.end_time, input.duration_seconds);
      const lastId = this.db.prepare('SELECT last_insert_rowid() as id').get() as { id: number };
      return this.idlePeriods.findById(lastId.id)!;
    },

    findAll(filters?: {
      from?: string;
      to?: string;
    }): IdlePeriod[] {
      let query = 'SELECT * FROM idle_periods';
      const conditions: string[] = [];
      const params: string[] = [];

      if (filters?.from) {
        conditions.push('start_time >= ?');
        params.push(filters.from);
      }
      if (filters?.to) {
        conditions.push('start_time <= ?');
        params.push(filters.to);
      }

      if (conditions.length > 0) {
        query += ' WHERE ' + conditions.join(' AND ');
      }

      query += ' ORDER BY start_time DESC';

      const stmt = this.db.prepare(query);
      return stmt.all(...params) as IdlePeriod[];
    },

    findById(id: number): IdlePeriod | undefined {
      const stmt = this.db.prepare(`
        SELECT * FROM idle_periods WHERE id = ?
      `);
      return stmt.get(id) as IdlePeriod | undefined;
    }
  };

  settings = {
    get(key: string): string | null {
      const stmt = this.db.prepare(`
        SELECT value FROM settings WHERE key = ?
      `);
      const row = stmt.get(key) as { value: string | null } | undefined;
      return row?.value ?? null;
    },

    set(key: string, value: string): void {
      const stmt = this.db.prepare(`
        INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
      `);
      stmt.run(key, value);
    }
  };
}