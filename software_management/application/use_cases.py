from __future__ import annotations

from dataclasses import dataclass

from software_management.domain.value_objects import FileHash, VersionNumber

from .dtos import (
    AdminSoftwareItem,
    AdminSummaryOutput,
    DeleteSoftwareInput,
    DeleteSoftwareOutput,
    DownloadSoftwareInput,
    DownloadSoftwareOutput,
    ListAdminSoftwareInput,
    ListSoftwareInput,
    ListVersionsInput,
    PublishVersionInput,
    PublishVersionOutput,
    SoftwareListItem,
    UploadSoftwareInput,
    UploadSoftwareOutput,
    VersionListItem,
)
from .errors import NotFoundError
from .interfaces import (
    AccessControlService,
    CreateVersionCommand,
    SoftwareRepository,
    StorageService,
    VirusScannerService,
)


@dataclass(slots=True)
class UploadSoftware:
    repository: SoftwareRepository
    storage: StorageService
    access_control: AccessControlService
    virus_scanner: VirusScannerService

    async def execute(self, dto: UploadSoftwareInput) -> UploadSoftwareOutput:
        VersionNumber(dto.version)
        await self.access_control.assert_upload_allowed(dto.actor_id)
        scanned_stream = self.virus_scanner.wrap_stream(
            dto.stream,
            file_name=dto.file_name,
            content_type=dto.content_type,
        )
        stored_object = await self.storage.store_stream(
            scanned_stream,
            file_name=dto.file_name,
            content_type=dto.content_type,
        )
        FileHash(stored_object.file_hash)
        command = CreateVersionCommand(
            actor_id=dto.actor_id,
            software_name=dto.software_name,
            software_description=dto.software_description,
            version=dto.version,
            artifact_storage_key=stored_object.storage_key,
            artifact_file_hash=stored_object.file_hash,
            artifact_size_bytes=stored_object.size_bytes,
            artifact_file_name=stored_object.file_name,
            artifact_content_type=stored_object.content_type,
            is_public=dto.is_public,
            software_id=dto.software_id,
            publish_now=dto.publish_now,
            expected_software_row_version=dto.expected_software_row_version,
        )
        try:
            result = await self.repository.create_version(command)
        except Exception:
            await self.storage.delete(stored_object.storage_key)
            raise
        return UploadSoftwareOutput(
            software_id=result.software_id,
            version_id=result.version_id,
            artifact_id=result.artifact_id,
            version=result.version,
            file_hash=stored_object.file_hash,
            size_bytes=stored_object.size_bytes,
            software_row_version=result.software_row_version,
            published=result.published,
        )


@dataclass(slots=True)
class PublishVersion:
    repository: SoftwareRepository
    access_control: AccessControlService

    async def execute(self, dto: PublishVersionInput) -> PublishVersionOutput:
        VersionNumber(dto.version)
        owner_id = await self.repository.get_software_owner(dto.software_id)
        if owner_id is None:
            raise NotFoundError("software not found")
        await self.access_control.assert_publish_allowed(dto.actor_id, owner_id)
        result = await self.repository.publish_version(
            actor_id=dto.actor_id,
            software_id=dto.software_id,
            version=dto.version,
            expected_software_row_version=dto.expected_software_row_version,
        )
        return PublishVersionOutput(
            software_id=result.software_id,
            version_id=result.version_id,
            version=result.version,
            published_at=result.published_at,
            software_row_version=result.software_row_version,
        )


@dataclass(slots=True)
class DownloadSoftware:
    repository: SoftwareRepository
    storage: StorageService
    access_control: AccessControlService
    chunk_size: int

    async def execute(self, dto: DownloadSoftwareInput) -> DownloadSoftwareOutput:
        VersionNumber(dto.version)
        descriptor = await self.repository.get_download_descriptor(dto.software_id, dto.version)
        if descriptor is None:
            raise NotFoundError("software version not found")
        await self.access_control.assert_download_allowed(
            dto.actor_id,
            descriptor.owner_id,
            descriptor.published,
        )
        stream = await self.storage.open_stream(
            descriptor.storage_key,
            chunk_size=self.chunk_size,
        )
        return DownloadSoftwareOutput(
            software_id=descriptor.software_id,
            version_id=descriptor.version_id,
            version=descriptor.version,
            file_name=descriptor.file_name,
            content_type=descriptor.content_type,
            size_bytes=descriptor.size_bytes,
            file_hash=descriptor.file_hash,
            stream=stream,
        )


@dataclass(slots=True)
class DeleteSoftware:
    repository: SoftwareRepository
    storage: StorageService
    access_control: AccessControlService

    async def execute(self, dto: DeleteSoftwareInput) -> DeleteSoftwareOutput:
        owner_id = await self.repository.get_software_owner(dto.software_id)
        if owner_id is None:
            raise NotFoundError("software not found")
        await self.access_control.assert_delete_allowed(dto.actor_id, owner_id)
        result = await self.repository.delete_software(
            actor_id=dto.actor_id,
            software_id=dto.software_id,
            expected_software_row_version=dto.expected_software_row_version,
        )
        for storage_key in result.storage_keys:
            await self.storage.delete(storage_key)
        return DeleteSoftwareOutput(
            software_id=result.software_id,
            deleted_versions=result.deleted_versions,
            deleted_artifacts=result.deleted_artifacts,
        )


@dataclass(slots=True)
class ListSoftware:
    repository: SoftwareRepository

    async def execute(self, dto: ListSoftwareInput) -> list[SoftwareListItem]:
        rows = await self.repository.list_softwares(
            dto.actor_id,
            offset=dto.offset,
            limit=dto.limit,
        )
        return [
            SoftwareListItem(
                id=row.id,
                owner_id=row.owner_id,
                name=row.name,
                description=row.description,
                is_public=row.is_public,
                latest_version=row.latest_version,
                latest_version_id=row.latest_version_id,
                download_count=row.latest_download_count,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]


@dataclass(slots=True)
class ListVersions:
    repository: SoftwareRepository

    async def execute(self, dto: ListVersionsInput) -> list[VersionListItem]:
        rows = await self.repository.list_versions(
            dto.actor_id,
            dto.software_id,
            limit=dto.limit,
        )
        return [
            VersionListItem(
                id=row.id,
                software_id=row.software_id,
                version=row.version,
                is_published=row.is_published,
                download_count=row.download_count,
                file_name=row.file_name,
                content_type=row.content_type,
                size_bytes=row.size_bytes,
                file_hash=row.file_hash,
                created_at=row.created_at,
                published_at=row.published_at,
            )
            for row in rows
        ]


@dataclass(slots=True)
class GetAdminSummary:
    repository: SoftwareRepository

    async def execute(self) -> AdminSummaryOutput:
        row = await self.repository.get_admin_summary()
        return AdminSummaryOutput(
            total_packages=row.total_packages,
            private_packages=row.private_packages,
            public_packages=row.public_packages,
            total_versions=row.total_versions,
            total_downloads=row.total_downloads,
        )


@dataclass(slots=True)
class ListAdminSoftware:
    repository: SoftwareRepository

    async def execute(self, dto: ListAdminSoftwareInput) -> list[AdminSoftwareItem]:
        rows = await self.repository.list_admin_softwares(offset=dto.offset, limit=dto.limit)
        return [
            AdminSoftwareItem(
                package_id=row.package_id,
                name=row.name,
                owner_id=row.owner_id,
                is_public=row.is_public,
                latest_version=row.latest_version,
                download_count=row.download_count,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]
