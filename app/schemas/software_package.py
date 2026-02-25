from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UploadSessionInitRequest(BaseModel):
    package_name: str = Field(min_length=1, max_length=150)
    package_description: str = Field(min_length=1, max_length=5000)
    package_category: str = Field(min_length=1, max_length=80)
    package_language: str = Field(min_length=1, max_length=80)
    package_version: str = Field(min_length=1, max_length=64)
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str | None = Field(default=None, max_length=120)
    is_public: bool = True
    max_size_bytes: int | None = None


class UploadSessionInitResponse(BaseModel):
    upload_id: str
    offset: int
    max_size_bytes: int


class UploadAppendResponse(BaseModel):
    upload_id: str
    offset: int
    status: str


class UploadCompleteResponse(BaseModel):
    upload_id: str
    file_version_id: int


class SoftwarePackageRead(BaseModel):
    id: int
    owner_id: int
    name: str
    description: str
    category: str
    language: str
    is_public: bool
    latest_version: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileVersionRead(BaseModel):
    id: int
    package_id: int
    file_name: str
    content_type: str | None
    version: str
    size_bytes: int
    checksum_sha256: str
    download_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SoftwarePackageAdminSummaryRead(BaseModel):
    total_packages: int
    private_packages: int
    public_packages: int
    total_versions: int
    total_downloads: int
    top_languages: list[dict]
    top_categories: list[dict]


class SoftwarePackageAdminItemRead(BaseModel):
    package_id: int
    name: str
    category: str
    language: str
    owner_id: int
    owner_username: str
    owner_email: str
    is_public: bool
    latest_version: str | None
    created_at: datetime
    updated_at: datetime
