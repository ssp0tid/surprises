"""Web dashboard router."""

from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_session
from ..models import Pipeline, Run, Task

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    return """<!DOCTYPE html>
<html>
<head>
    <title>Local Pipeline</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Local Pipeline</h1>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/pipelines">Pipelines</a>
                <a href="/runs">Runs</a>
            </nav>
        </header>
        <main>
            <h2>Welcome to Local Pipeline</h2>
            <p>A YAML-based local task pipeline/orchestrator</p>
            <div class="stats">
                <div class="stat-card">
                    <h3>Pipelines</h3>
                    <p class="stat-value" id="pipeline-count">-</p>
                </div>
                <div class="stat-card">
                    <h3>Total Runs</h3>
                    <p class="stat-value" id="run-count">-</p>
                </div>
                <div class="stat-card">
                    <h3>Running</h3>
                    <p class="stat-value" id="running-count">-</p>
                </div>
                <div class="stat-card">
                    <h3>Success Rate</h3>
                    <p class="stat-value" id="success-rate">-</p>
                </div>
            </div>
        </main>
    </div>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>"""


@router.get("/pipelines", response_class=HTMLResponse)
async def list_pipelines(request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Pipeline).order_by(Pipeline.created_at.desc()))
    pipelines = result.scalars().all()

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Pipelines - Local Pipeline</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Local Pipeline</h1>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/pipelines">Pipelines</a>
                <a href="/runs">Runs</a>
            </nav>
        </header>
        <main>
            <h2>Pipelines</h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Version</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>"""

    for p in pipelines:
        status = "Active" if p.is_active else "Inactive"
        html += f"""
                    <tr>
                        <td>{p.name}</td>
                        <td>{p.version}</td>
                        <td><span class="badge {status.lower()}">{status}</span></td>
                        <td>{p.created_at.strftime("%Y-%m-%d %H:%M")}</td>
                        <td>
                            <a href="/pipelines/{p.id}" class="btn">View</a>
                            <button onclick="triggerPipeline('{p.id}')" class="btn btn-primary">Trigger</button>
                        </td>
                    </tr>"""

    html += """                </tbody>
            </table>
        </main>
    </div>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>"""
    return html


@router.get("/pipelines/{pipeline_id}", response_class=HTMLResponse)
async def pipeline_detail(
    request: Request, pipeline_id: str, session: AsyncSession = Depends(get_session)
):
    pipeline = await session.get(Pipeline, pipeline_id)
    if not pipeline:
        return HTMLResponse("<h1>Pipeline not found</h1>", status_code=404)

    result = await session.execute(
        select(Run).where(Run.pipeline_id == pipeline_id).order_by(Run.created_at.desc()).limit(10)
    )
    runs = result.scalars().all()

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{pipeline.name} - Local Pipeline</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Local Pipeline</h1>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/pipelines">Pipelines</a>
                <a href="/runs">Runs</a>
            </nav>
        </header>
        <main>
            <h2>{pipeline.name}</h2>
            <p>{pipeline.description or "No description"}</p>
            <p>Version: {pipeline.version}</p>
            <button onclick="triggerPipeline('{pipeline.id}')" class="btn btn-primary">Trigger Pipeline</button>

            <h3>Recent Runs</h3>
            <table>
                <thead>
                    <tr>
                        <th>Run #</th>
                        <th>Status</th>
                        <th>Triggered By</th>
                        <th>Duration</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>"""

    for r in runs:
        duration = f"{r.duration_ms}ms" if r.duration_ms else "-"
        html += f"""
                    <tr>
                        <td>{r.run_number}</td>
                        <td><span class="badge {r.status}">{r.status}</span></td>
                        <td>{r.triggered_by}</td>
                        <td>{duration}</td>
                        <td>{r.created_at.strftime("%Y-%m-%d %H:%M")}</td>
                        <td><a href="/runs/{r.id}" class="btn">View</a></td>
                    </tr>"""

    html += """                </tbody>
            </table>
        </main>
    </div>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>"""
    return html


@router.get("/runs", response_class=HTMLResponse)
async def list_runs(request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Run).options(selectinload(Run.pipeline)).order_by(Run.created_at.desc()).limit(50)
    )
    runs = result.scalars().all()

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Runs - Local Pipeline</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Local Pipeline</h1>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/pipelines">Pipelines</a>
                <a href="/runs">Runs</a>
            </nav>
        </header>
        <main>
            <h2>All Runs</h2>
            <table>
                <thead>
                    <tr>
                        <th>Pipeline</th>
                        <th>Run #</th>
                        <th>Status</th>
                        <th>Triggered By</th>
                        <th>Duration</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>"""

    for r in runs:
        duration = f"{r.duration_ms}ms" if r.duration_ms else "-"
        pipeline_name = r.pipeline.name if r.pipeline else "Unknown"
        html += f"""
                    <tr>
                        <td>{pipeline_name}</td>
                        <td>{r.run_number}</td>
                        <td><span class="badge {r.status}">{r.status}</span></td>
                        <td>{r.triggered_by}</td>
                        <td>{duration}</td>
                        <td>{r.created_at.strftime("%Y-%m-%d %H:%M")}</td>
                        <td><a href="/runs/{r.id}" class="btn">View</a></td>
                    </tr>"""

    html += """                </tbody>
            </table>
        </main>
    </div>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>"""
    return html


@router.get("/runs/{run_id}", response_class=HTMLResponse)
async def run_detail(request: Request, run_id: str, session: AsyncSession = Depends(get_session)):
    run = await session.get(Run, run_id)
    if not run:
        return HTMLResponse("<h1>Run not found</h1>", status_code=404)

    pipeline = await session.get(Pipeline, run.pipeline_id)

    result = await session.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.created_at)
    )
    tasks = result.scalars().all()

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Run #{run.run_number} - Local Pipeline</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Local Pipeline</h1>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/pipelines">Pipelines</a>
                <a href="/runs">Runs</a>
            </nav>
        </header>
        <main>
            <h2>Run #{run.run_number}</h2>
            <p>Pipeline: <a href="/pipelines/{pipeline.id}">{pipeline.name}</a></p>
            <p>Status: <span class="badge {run.status}">{run.status}</span></p>
            <p>Triggered By: {run.triggered_by}</p>
            <p>Duration: {run.duration_ms}ms</p>
            <p>Started: {run.started_at.strftime("%Y-%m-%d %H:%M:%S") if run.started_at else "-"}</p>
            <p>Finished: {run.finished_at.strftime("%Y-%m-%d %H:%M:%S") if run.finished_at else "-"}</p>

            <h3>Tasks</h3>
            <table>
                <thead>
                    <tr>
                        <th>Task</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Attempts</th>
                    </tr>
                </thead>
                <tbody>"""

    for t in tasks:
        duration = f"{t.duration_ms}ms" if t.duration_ms else "-"
        html += f"""
                    <tr>
                        <td>{t.name}</td>
                        <td>{t.task_type}</td>
                        <td><span class="badge {t.status}">{t.status}</span></td>
                        <td>{duration}</td>
                        <td>{t.attempt}</td>
                    </tr>"""

    html += """                </tbody>
            </table>
        </main>
    </div>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>"""
    return html
