from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter

from software_management.application.use_cases import (
    DeleteSoftware,
    DownloadSoftware,
    GetAdminSummary,
    ListAdminSoftware,
    ListSoftware,
    ListVersions,
    PublishVersion,
    UploadSoftware,
)
from software_management.infrastructure import (
    AccessControlAdapter,
    AsyncDatabase,
    AsyncVirusScannerAdapter,
    DatabaseConfig,
    LocalAsyncStorageService,
    LocalStorageConfig,
    SQLAlchemySoftwareRepository,
)
from software_management.presentation import create_router


def install_uvloop() -> None:
    try:
        import uvloop  # type: ignore
    except Exception:
        return
    try:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except Exception:
        return


@dataclass(frozen=True, slots=True)
class SMSBootstrapConfig:
    database_url: str
    storage_root: Path
    upload_chunk_size: int = 1024 * 1024
    pool_size: int = 20
    max_overflow: int = 40
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo_sql: bool = False


@dataclass(slots=True)
class SMSModule:
    router: APIRouter
    database: AsyncDatabase

    async def initialize(self) -> None:
        await self.database.create_schema()

    async def close(self) -> None:
        await self.database.dispose()


def build_sms_module(
    *,
    config: SMSBootstrapConfig,
    current_actor_dependency: Callable[..., Any],
) -> SMSModule:
    install_uvloop()
    database = AsyncDatabase(
        DatabaseConfig(
            database_url=config.database_url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            echo=config.echo_sql,
        )
    )
    repository = SQLAlchemySoftwareRepository(database.sessionmaker)
    storage = LocalAsyncStorageService(
        LocalStorageConfig(root=config.storage_root)
    )
    access_control = AccessControlAdapter()
    virus_scanner = AsyncVirusScannerAdapter()

    upload_software = UploadSoftware(
        repository=repository,
        storage=storage,
        access_control=access_control,
        virus_scanner=virus_scanner,
    )
    publish_version = PublishVersion(repository=repository, access_control=access_control)
    download_software = DownloadSoftware(
        repository=repository,
        storage=storage,
        access_control=access_control,
        chunk_size=config.upload_chunk_size,
    )
    delete_software = DeleteSoftware(
        repository=repository,
        storage=storage,
        access_control=access_control,
    )
    list_software = ListSoftware(repository=repository)
    list_versions = ListVersions(repository=repository)
    get_admin_summary = GetAdminSummary(repository=repository)
    list_admin_software = ListAdminSoftware(repository=repository)
    router = create_router(
        upload_software=upload_software,
        publish_version=publish_version,
        download_software=download_software,
        delete_software=delete_software,
        list_software=list_software,
        list_versions=list_versions,
        get_admin_summary=get_admin_summary,
        list_admin_software=list_admin_software,
        current_actor_dependency=current_actor_dependency,
        upload_chunk_size=config.upload_chunk_size,
    )
    return SMSModule(router=router, database=database)
