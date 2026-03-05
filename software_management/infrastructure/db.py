from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .models import SMSBase


def normalize_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    raise ValueError("unsupported async database URL")


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    database_url: str
    pool_size: int = 20
    max_overflow: int = 40
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False


class AsyncDatabase:
    def __init__(self, config: DatabaseConfig) -> None:
        self._engine: AsyncEngine = create_async_engine(
            normalize_async_database_url(config.database_url),
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=True,
            echo=config.echo,
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        return self._sessionmaker

    async def create_schema(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(SMSBase.metadata.create_all)

    async def dispose(self) -> None:
        await self._engine.dispose()
