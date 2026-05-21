import { Router, Request, Response, NextFunction } from 'express';
import { Repository } from '../../db/repository.js';
import {
  validateDate,
  validateRequired,
  validateDateRange,
  createError,
  ERROR_CODES
} from '../middleware/error-handler.js';
import { SessionsResponse, TimeSession } from '../../types/index.js';

export interface SessionsRouterDeps {
  repository: Repository;
}

export function createSessionsRouter({ repository }: SessionsRouterDeps): Router {
  const router = Router();

  router.get('/', (req: Request, res: Response, next: NextFunction) => {
    try {
      const { from, to, project_id } = req.query;

      if (from && typeof from === 'string') {
        validateDate(from, 'from');
      }
      if (to && typeof to === 'string') {
        validateDate(to, 'to');
      }
      if (from && to) {
        validateDateRange(from as string, to as string);
      }

      const filters: { from?: string; to?: string; project_id?: string } = {};
      if (from && typeof from === 'string') filters.from = from;
      if (to && typeof to === 'string') filters.to = to;
      if (project_id && typeof project_id === 'string') filters.project_id = project_id;

      const sessions = repository.sessions.findAll(filters);

      const totalDuration = sessions.reduce((sum, session) => {
        return sum + (session.duration_seconds ?? 0);
      }, 0);

      const response: SessionsResponse = {
        sessions: sessions.map(mapSessionToTimeSession),
        totalDuration
      };

      res.json(response);
    } catch (error) {
      next(error);
    }
  });

  router.post('/', (req: Request, res: Response, next: NextFunction) => {
    try {
      const { project_id, start_time, end_time, window_title } = req.body;

      validateRequired(project_id, 'project_id');
      validateRequired(start_time, 'start_time');

      const projectId = String(project_id);
      const startTime = String(start_time);
      const endTime = end_time ? String(end_time) : undefined;
      const windowTitle = window_title ? String(window_title) : undefined;

      let durationSeconds: number | undefined;
      if (endTime) {
        const start = new Date(startTime);
        const end = new Date(endTime);
        durationSeconds = Math.floor((end.getTime() - start.getTime()) / 1000);
        if (durationSeconds < 0) {
          throw createError(
            ERROR_CODES.VALIDATION_ERROR,
            'Invalid session times',
            { field: 'end_time', reason: 'Must be after start_time' }
          );
        }
      }

      const session = repository.sessions.insert({
        project_id: projectId,
        start_time: startTime,
        end_time: endTime,
        duration_seconds: durationSeconds,
        window_title: windowTitle
      });

      res.status(201).json(mapSessionToTimeSession(session));
    } catch (error) {
      next(error);
    }
  });

  router.delete('/:id', (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = parseInt(req.params.id, 10);
      if (isNaN(id)) {
        throw createError(
          ERROR_CODES.VALIDATION_ERROR,
          'Invalid session ID',
          { field: 'id', reason: 'Must be a number' }
        );
      }

      const deleted = repository.sessions.delete(id);
      if (!deleted) {
        throw createError(
          ERROR_CODES.RESOURCE_NOT_FOUND,
          'Session not found',
          { field: 'id', reason: 'Session does not exist' },
          404
        );
      }

      res.json({ deleted: true });
    } catch (error) {
      next(error);
    }
  });

  return router;
}

function mapSessionToTimeSession(session: {
  id: number;
  project_id: string | null;
  start_time: string;
  end_time: string | null;
  duration_seconds: number | null;
  window_title: string | null;
  created_at: string;
}): TimeSession {
  return {
    id: session.id,
    projectId: session.project_id ?? '',
    startTime: new Date(session.start_time),
    endTime: session.end_time ? new Date(session.end_time) : null,
    durationSeconds: session.duration_seconds,
    windowTitle: session.window_title,
    createdAt: new Date(session.created_at)
  };
}