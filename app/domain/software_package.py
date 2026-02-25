from __future__ import annotations

from dataclasses import dataclass

from app.exceptions.exceptions import ValidationError


@dataclass(frozen=True)
class SoftwarePackageDraft:
    owner_id: int
    name: str
    description: str
    category: str
    language: str
    version: str
    file_name: str
    content_type: str | None
    is_public: bool

    def validate(self) -> None:
        if self.owner_id <= 0:
            raise ValidationError("Invalid package owner")
        if not self.name.strip():
            raise ValidationError("Package name is required")
        if not self.description.strip():
            raise ValidationError("Package description is required")
        if not self.category.strip():
            raise ValidationError("Package category is required")
        if not self.language.strip():
            raise ValidationError("Project language is required")
        if not self.version.strip():
            raise ValidationError("Package version is required")
        if not self.file_name.strip():
            raise ValidationError("Uploaded file name is required")


@dataclass(frozen=True)
class FileVersionDraft:
    version: str
    checksum_sha256: str
    size_bytes: int

    def validate(self) -> None:
        if not self.version.strip():
            raise ValidationError("Package version is required")
        if len(self.checksum_sha256) != 64:
            raise ValidationError("SHA-256 checksum is required")
        if self.size_bytes <= 0:
            raise ValidationError("Package file is empty")
