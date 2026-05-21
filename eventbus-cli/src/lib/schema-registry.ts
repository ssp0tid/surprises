import Ajv from "ajv";
import addFormats from "ajv-formats";
import type { Storage } from "./storage.js";
import { SchemaValidationError } from "./errors.js";

export interface SchemaEntry {
  eventType: string;
  version: string;
  schema: object;
  createdAt: string;
}

const ajv = new Ajv({ allErrors: true, verbose: true });
addFormats(ajv);

export class SchemaRegistry {
  private storage: Storage;
  private cache: Map<string, SchemaEntry> = new Map();
  private validators: Map<string, ReturnType<typeof ajv.compile>> = new Map();

  constructor(storage: Storage) {
    this.storage = storage;
    this.loadFromStorage();
  }

  private loadFromStorage(): void {
    try {
      const channels = this.storage.listChannels();
      for (const channel of channels) {
        const events = this.storage.getEvents(channel, { limit: 1000 });
        for (const event of events) {
          this.cache.set(event.type, {
            eventType: event.type,
            version: event.version,
            schema: event.payload as object,
            createdAt: event.timestamp,
          });
        }
      }
    } catch {}
  }

  register(eventType: string, version: string, schema: object): void {
    const entry: SchemaEntry = {
      eventType,
      version,
      schema,
      createdAt: new Date().toISOString(),
    };
    this.cache.set(`${eventType}:${version}`, entry);
    this.validators.delete(`${eventType}:${version}`);
  }

  get(eventType: string, version: string = "v1"): SchemaEntry | undefined {
    return this.cache.get(`${eventType}:${version}`);
  }

  validate(event: unknown, eventType: string, version: string = "v1"): void {
    const entry = this.get(eventType, version);
    if (!entry) {
      return;
    }

    let validator = this.validators.get(`${eventType}:${version}`);
    if (!validator) {
      validator = ajv.compile(entry.schema);
      this.validators.set(`${eventType}:${version}`, validator);
    }

    if (!validator(event)) {
      throw new SchemaValidationError(validator.errors || []);
    }
  }

  list(): SchemaEntry[] {
    return Array.from(this.cache.values());
  }

  clear(): void {
    this.cache.clear();
    this.validators.clear();
  }
}
