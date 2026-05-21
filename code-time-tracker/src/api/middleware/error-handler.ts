import { Request, Response, NextFunction } from 'express';
import { ErrorResponse } from '../../types/index.js';

export const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  INVALID_DATE: 'INVALID_DATE',
  REQUIRED_FIELD: 'REQUIRED_FIELD',
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  INVALID_REQUEST: 'INVALID_REQUEST'
} as const;

export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];

export interface AppError extends Error {
  code: ErrorCode;
  statusCode: number;
  details?: Record<string, unknown>;
}

export function createError(
  code: ErrorCode,
  message: string,
  details?: Record<string, unknown>,
  statusCode: number = 400
): AppError {
  const error = new Error(message) as AppError;
  error.code = code;
  error.statusCode = statusCode;
  error.details = details;
  return error;
}

export function errorHandler(
  err: Error | AppError,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  const isAppError = 'code' in err && 'statusCode' in err;

  const statusCode = isAppError ? (err as AppError).statusCode : 500;
  const code = isAppError ? (err as AppError).code : 'INVALID_REQUEST';
  const message = err.message || 'An unexpected error occurred';
  const details = isAppError ? (err as AppError).details : undefined;

  const errorResponse: ErrorResponse = {
    error: {
      code,
      message,
      ...(details && { details })
    }
  };

  res.status(statusCode).json(errorResponse);
}

export function validateDate(dateStr: string, fieldName: string): void {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) {
    throw createError(
      ERROR_CODES.INVALID_DATE,
      `Invalid ${fieldName} date format`,
      { field: fieldName, reason: 'Must be a valid ISO 8601 date' }
    );
  }
}

export function validateRequired(
  value: unknown,
  fieldName: string
): void {
  if (value === undefined || value === null || value === '') {
    throw createError(
      ERROR_CODES.REQUIRED_FIELD,
      `${fieldName} is required`,
      { field: fieldName, reason: 'This field is required' }
    );
  }
}

export function validateDateRange(from?: string, to?: string): void {
  if (from && to) {
    const fromDate = new Date(from);
    const toDate = new Date(to);
    if (fromDate > toDate) {
      throw createError(
        ERROR_CODES.INVALID_DATE,
        'Invalid date range',
        { field: 'from', reason: "Must be before 'to' date" }
      );
    }
  }
}

export function parseOptionalDate(dateStr?: string): Date | undefined {
  if (!dateStr) return undefined;
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) {
    throw createError(
      ERROR_CODES.INVALID_DATE,
      'Invalid date format',
      { field: dateStr, reason: 'Must be a valid ISO 8601 date' }
    );
  }
  return date;
}