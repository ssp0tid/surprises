"""Main application entry point."""

import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .config import config
from .database import init_db
from .api.routes import router as api_router
from .api.webhooks import router as webhook_router
from .web.router import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    Path("data").mkdir(exist_ok=True)
    yield


app = FastAPI(
    title="Local Pipeline",
    description="YAML-based local task pipeline/orchestrator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
app.include_router(webhook_router)
app.include_router(web_router)

static_path = Path(__file__).parent.parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


def main():
    import uvicorn

    uvicorn.run(
        "local_pipeline.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
