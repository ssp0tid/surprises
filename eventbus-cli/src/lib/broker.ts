import { EventEmitter } from "node:events";
import type { Storage } from "./storage.js";
import type { SchemaRegistry } from "./schema-registry.js";
import { ChannelManager } from "./channel.js";
import type { Event, RawEvent } from "./event.js";
import { createEvent } from "./event.js";
import type { Subscription } from "./channel.js";
import type { FilterAST } from "./channel.js";

export class EventBroker {
  private storage: Storage;
  private schemaRegistry: SchemaRegistry;
  private channelManager: ChannelManager;
  private emitter: EventEmitter;

  constructor(storage: Storage, schemaRegistry: SchemaRegistry) {
    this.storage = storage;
    this.schemaRegistry = schemaRegistry;
    this.channelManager = new ChannelManager();
    this.emitter = new EventEmitter();
  }

  async publish(
    channel: string,
    type: string,
    payload: object,
    metadata?: object,
  ): Promise<Event> {
    const rawEvent: RawEvent = {
      channel,
      type,
      payload,
      metadata,
      timestamp: new Date().toISOString(),
      version: "v1",
    };

    const event = createEvent(rawEvent);

    this.schemaRegistry.validate(event, type, event.version);

    const stored = this.storage.insertEvent(event);

    this.channelManager.deliver(stored);
    this.emitter.emit(channel, stored);
    this.emitter.emit("*", stored);

    return stored;
  }

  subscribe(
    channelPattern: string,
    callback: (event: Event) => void,
    filter?: FilterAST,
  ): Subscription {
    const savedCallback = (event: Event) => {
      if (!filter || this.channelManager.filterEvent(event, filter)) {
        callback(event);
      }
    };

    return this.channelManager.subscribe(channelPattern, savedCallback, filter);
  }

  unsubscribe(subscription: Subscription): void {
    this.channelManager.unsubscribe(subscription);
  }

  getEvents(
    channelPattern: string,
    options: {
      from?: string;
      to?: string;
      limit?: number;
    } = {},
  ): Event[] {
    return this.storage.getEvents(channelPattern, options);
  }

  listChannels(): string[] {
    return this.storage.listChannels();
  }

  onChannel(channel: string, callback: (event: Event) => void): void {
    this.emitter.on(channel, callback);
  }

  onAnyChannel(callback: (event: Event) => void): void {
    this.emitter.on("*", callback);
  }

  close(): void {
    this.storage.close();
  }
}
