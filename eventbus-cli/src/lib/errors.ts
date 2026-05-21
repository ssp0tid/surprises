export class EventbusError extends Error {
  constructor(
    message: string,
    public code: string,
  ) {
    super(message);
    this.name = "EventbusError";
  }
}

export class ChannelNotFoundError extends EventbusError {
  constructor(channel: string) {
    super(`Channel not found: ${channel}`, "CHANNEL_NOT_FOUND");
    this.name = "ChannelNotFoundError";
  }
}

export class SchemaValidationError extends EventbusError {
  public errors: unknown[];

  constructor(errors: unknown[]) {
    super(
      `Schema validation failed: ${errors.length} error(s)`,
      "INVALID_EVENT",
    );
    this.name = "SchemaValidationError";
    this.errors = errors;
  }
}

export class DuplicateChannelError extends EventbusError {
  constructor(channel: string) {
    super(`Channel already exists: ${channel}`, "DUPLICATE_CHANNEL");
    this.name = "DuplicateChannelError";
  }
}

export class InvalidPatternError extends EventbusError {
  constructor(pattern: string) {
    super(`Invalid channel pattern: ${pattern}`, "INVALID_PATTERN");
    this.name = "InvalidPatternError";
  }
}

export class InvalidChannelError extends EventbusError {
  constructor(channel: string) {
    super(
      `Invalid channel name: ${channel}. Use only letters, dots, and asterisks.`,
      "INVALID_CHANNEL",
    );
    this.name = "InvalidChannelError";
  }
}

export class InvalidEventTypeError extends EventbusError {
  constructor(eventType: string) {
    super(
      `Invalid event type: ${eventType}. Use only letters, dots, and numbers.`,
      "INVALID_EVENT_TYPE",
    );
    this.name = "InvalidEventTypeError";
  }
}

export class ServerError extends EventbusError {
  constructor(message: string) {
    super(message, "SERVER_ERROR");
    this.name = "ServerError";
  }
}

// Error code to HTTP status mapping
export const errorToHttpStatus: Record<string, number> = {
  INVALID_CHANNEL: 400,
  INVALID_EVENT: 400,
  CHANNEL_NOT_FOUND: 404,
  DUPLICATE_CHANNEL: 409,
  INVALID_PATTERN: 400,
  SERVER_ERROR: 500,
};
