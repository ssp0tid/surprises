import {
  EventbusError,
  InvalidChannelError,
  InvalidEventTypeError,
} from "./errors.js";

export interface Event {
  id: number;
  channel: string;
  type: string;
  payload: object;
  metadata?: object;
  timestamp: string;
  version: string;
}

export interface RawEvent {
  channel: string;
  type: string;
  payload: object;
  metadata?: object;
  timestamp?: string;
  version?: string;
}

const CHANNEL_REGEX = /^[a-zA-Z0-9.*]+$/;
const EVENT_TYPE_REGEX = /^[a-zA-Z0-9.]+$/;

export function validateChannel(channel: string): void {
  if (!channel || !CHANNEL_REGEX.test(channel)) {
    throw new InvalidChannelError(channel);
  }
}

export function validateEventType(eventType: string): void {
  if (!eventType || !EVENT_TYPE_REGEX.test(eventType)) {
    throw new InvalidEventTypeError(eventType);
  }
}

export function validateEventPayload(payload: unknown): void {
  if (payload === undefined || payload === null) {
    throw new EventbusError(
      "Payload cannot be null or undefined",
      "INVALID_EVENT",
    );
  }
  if (typeof payload !== "object") {
    throw new EventbusError(
      "Payload must be a valid JSON object",
      "INVALID_EVENT",
    );
  }
}

export function createEvent(raw: RawEvent): Event {
  validateChannel(raw.channel);
  validateEventType(raw.type);
  validateEventPayload(raw.payload);

  return {
    id: 0,
    channel: raw.channel,
    type: raw.type,
    payload: raw.payload,
    metadata: raw.metadata,
    timestamp: raw.timestamp || new Date().toISOString(),
    version: raw.version || "v1",
  };
}
