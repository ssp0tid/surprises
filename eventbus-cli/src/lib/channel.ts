import micromatch from "micromatch";
import type { Event } from "./event.js";

export interface Subscription {
  id: string;
  pattern: string;
  callback: (event: Event) => void;
  filter?: FilterAST;
}

export interface FilterAST {
  type: "comparison" | "logical";
  operator?: ">" | "<" | ">=" | "<=" | "==" | "!=";
  field?: string;
  value?: unknown;
  left?: FilterAST;
  right?: FilterAST;
  operator2?: "and" | "or";
}

export class ChannelManager {
  private subscribers: Map<string, Set<Subscription>> = new Map();

  subscribe(
    pattern: string,
    callback: (event: Event) => void,
    filter?: FilterAST,
  ): Subscription {
    const subscription: Subscription = {
      id: Math.random().toString(36).substring(2, 15),
      pattern,
      callback,
      filter,
    };

    if (!this.subscribers.has(pattern)) {
      this.subscribers.set(pattern, new Set());
    }
    this.subscribers.get(pattern)!.add(subscription);

    return subscription;
  }

  unsubscribe(subscription: Subscription): void {
    const subs = this.subscribers.get(subscription.pattern);
    if (subs) {
      subs.delete(subscription);
      if (subs.size === 0) {
        this.subscribers.delete(subscription.pattern);
      }
    }
  }

  deliver(event: Event): void {
    for (const [pattern, subs] of this.subscribers) {
      if (this.matchChannel(event.channel, pattern)) {
        for (const sub of subs) {
          if (!sub.filter || this.filterEvent(event, sub.filter)) {
            try {
              sub.callback(event);
            } catch (err) {
              console.error("Subscriber error:", err);
            }
          }
        }
      }
    }
  }

  matchChannel(eventChannel: string, subPattern: string): boolean {
    if (eventChannel === subPattern) {
      return true;
    }

    if (subPattern.includes("*")) {
      const pattern = subPattern.replace(/\./g, "\\.");
      return micromatch.isMatch(eventChannel, pattern);
    }

    return false;
  }

  filterEvent(event: Event, filter: FilterAST): boolean {
    if (filter.type === "comparison") {
      const fieldValue = this.getFieldValue(event, filter.field || "");
      return this.compare(fieldValue, filter.operator || "==", filter.value);
    }

    if (filter.type === "logical") {
      const left = filter.left ? this.filterEvent(event, filter.left) : true;
      const right = filter.right ? this.filterEvent(event, filter.right) : true;

      if (filter.operator2 === "and") {
        return left && right;
      }
      if (filter.operator2 === "or") {
        return left || right;
      }
    }

    return true;
  }

  private getFieldValue(event: Event, field: string): unknown {
    if (field.startsWith("payload.")) {
      const key = field.substring(8);
      return (event.payload as Record<string, unknown>)[key];
    }
    if (field === "channel") {
      return event.channel;
    }
    if (field === "type") {
      return event.type;
    }
    return (event as unknown as Record<string, unknown>)[field];
  }

  private compare(left: unknown, operator: string, right: unknown): boolean {
    switch (operator) {
      case "==":
        return left === right;
      case "!=":
        return left !== right;
      case ">":
        return Number(left) > Number(right);
      case "<":
        return Number(left) < Number(right);
      case ">=":
        return Number(left) >= Number(right);
      case "<=":
        return Number(left) <= Number(right);
      default:
        return false;
    }
  }

  parseFilter(filterStr: string): FilterAST | undefined {
    if (!filterStr) {
      return undefined;
    }

    const andParts = filterStr.split(/\s+and\s+/i);
    if (andParts.length > 1) {
      return {
        type: "logical",
        operator2: "and",
        left: this.parseComparisonFilter(andParts[0]),
        right: this.parseComparisonFilter(andParts.slice(1).join(" and ")),
      };
    }

    const orParts = filterStr.split(/\s+or\s+/i);
    if (orParts.length > 1) {
      return {
        type: "logical",
        operator2: "or",
        left: this.parseComparisonFilter(orParts[0]),
        right: this.parseComparisonFilter(orParts.slice(1).join(" or ")),
      };
    }

    return this.parseComparisonFilter(filterStr);
  }

  private parseComparisonFilter(filterStr: string): FilterAST | undefined {
    const match = filterStr.match(/(\S+)\s*(==|!=|>|<|>=|<=)\s*(.+)/);
    if (!match) {
      return undefined;
    }

    const [, field, operator, value] = match;
    const trimmedValue = value.trim();
    let parsedValue: unknown;

    if (trimmedValue.startsWith('"') && trimmedValue.endsWith('"')) {
      parsedValue = trimmedValue.slice(1, -1);
    } else if (trimmedValue === "true") {
      parsedValue = true;
    } else if (trimmedValue === "false") {
      parsedValue = false;
    } else if (!isNaN(Number(trimmedValue))) {
      parsedValue = Number(trimmedValue);
    }

    return {
      type: "comparison",
      field: field.trim(),
      operator: operator as FilterAST["operator"],
      value: parsedValue,
    };
  }
}
