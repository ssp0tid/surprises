"""Database setup and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from .config import config
from .models import Base


engine = create_async_engine(config.database.url, echo=False, future=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


sync_engine = create_engine(
    config.database.url.replace("+aiosqlite", "").replace("asyncpg", ""), echo=False
)
sync_session_factory = sessionmaker(bind=sync_engine)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_sync_session():
    with sync_session_factory() as session:
        yield session
