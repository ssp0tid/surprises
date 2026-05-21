import { HttpRequest, StepResult, ExecutionContext } from './types.js';
import { StepExecutionError, TimeoutError, SecurityError } from './errors.js';
import { VariableStore } from './variables.js';

const BLOCKED_HOSTS = [
  'localhost',
  '127.0.0.1',
  '0.0.0.0',
  '::1',
  '169.254.169.254',
  'metadata.google.internal',
];

export async function executeHttpStep(
  stepId: string,
  request: HttpRequest,
  timeout: number,
  context: ExecutionContext
): Promise<StepResult> {
  const startTime = Date.now();
  const store = new VariableStore(context.input, process.env as Record<string, string>);
  const url = store.interpolate(request.url, context);
  validateUrl(url);
  const headers: Record<string, string> = {};
  if (request.headers) {
    for (const [key, value] of Object.entries(request.headers)) {
      headers[key] = store.interpolate(value, context);
    }
  }
  let body: string | undefined;
  if (request.body) {
    const bodyContent = typeof request.body === 'string'
      ? store.interpolate(request.body, context)
      : JSON.stringify(request.body);
    if (!headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    body = bodyContent;
  }
  let query = '';
  if (request.query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(request.query)) {
      params.append(key, store.interpolate(value, context));
    }
    query = '?' + params.toString();
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url + query, {
      method: request.method,
      headers,
      body,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    let responseBody: any;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        responseBody = await response.json();
      } catch {
        responseBody = await response.text();
      }
    } else {
      responseBody = await response.text();
    }
    const duration = Date.now() - startTime;
    if (!response.ok) {
      return {
        stepId,
        status: 'failure',
        data: {
          status: response.status,
          statusText: response.statusText,
          body: responseBody,
        },
        duration,
      };
    }
    return {
      stepId,
      status: 'success',
      data: {
        status: response.status,
        statusText: response.statusText,
        body: responseBody,
      },
      duration,
    };
  } catch (error) {
    clearTimeout(timeoutId);
    const duration = Date.now() - startTime;
    if (error instanceof Error && error.name === 'AbortError') {
      throw new TimeoutError(stepId, timeout);
    }
    throw new StepExecutionError(
      `HTTP request failed: ${error}`,
      stepId,
      undefined,
      undefined,
      true
    );
  }
}

function validateUrl(url: string): void {
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new SecurityError(`Invalid protocol: ${parsed.protocol}`, 'protocol');
    }
    if (BLOCKED_HOSTS.some(host => parsed.hostname === host || parsed.hostname.endsWith('.' + host))) {
      throw new SecurityError(`Blocked host: ${parsed.hostname}`, 'blocked-host');
    }
    if (parsed.hostname.match(/^10\./) || parsed.hostname.match(/^172\.(1[6-9]|2[0-9]|3[0-1])\./) || parsed.hostname.match(/^192\.168\./)) {
      throw new SecurityError(`Blocked IP range: ${parsed.hostname}`, 'blocked-ip');
    }
  } catch (error) {
    if (error instanceof SecurityError) throw error;
    throw new SecurityError(`Invalid URL: ${url}`, 'invalid-url');
  }
}