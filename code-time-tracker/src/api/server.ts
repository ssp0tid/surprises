import express, { Express, Request, Response, NextFunction } from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const APP_VERSION = '1.0.0';
const SERVER_START_TIME = new Date();

interface DaemonState {
  status: 'running' | 'paused';
  lastSessionAt: Date | null;
  isCurrentlyFocused: boolean;
  currentProject: { id: string; name: string } | null;
}

const daemonState: DaemonState = {
  status: 'running',
  lastSessionAt: null,
  isCurrentlyFocused: false,
  currentProject: null,
};

export const app: Express = express();

app.use(express.json());

const publicPath = path.join(__dirname, '../../public');
app.use(express.static(publicPath));

app.get('/api/v1/health', (_req: Request, res: Response) => {
  const uptimeSeconds = Math.floor(
    (Date.now() - SERVER_START_TIME.getTime()) / 1000
  );

  res.json({
    status: daemonState.status,
    version: APP_VERSION,
    uptime_seconds: uptimeSeconds,
    last_session_at: daemonState.lastSessionAt?.toISOString() ?? null,
    is_currently_focused: daemonState.isCurrentlyFocused,
    current_project: daemonState.currentProject,
  });
});

app.use((_req: Request, res: Response) => {
  res.status(404).json({
    error: {
      code: 'NOT_FOUND',
      message: 'Route not found',
    },
  });
});

app.use(
  (
    err: Error,
    _req: Request,
    res: Response,
    _next: NextFunction
  ): Response => {
    console.error('Unhandled error:', err);
    return res.status(500).json({
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Internal server error',
      },
    });
  }
);

const PORT = 3737;
const HOST = 'localhost';

if (import.meta.url === process.argv[1]) {
  app.listen(PORT, HOST, () => {
    console.log(`API server running at http://${HOST}:${PORT}`);
    console.log(`Health endpoint: http://${HOST}:${PORT}/api/v1/health`);
  });
}

export default app;