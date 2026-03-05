from __future__ import annotations

from software_management.application.errors import ForbiddenError
from software_management.application.interfaces import AccessControlService


class AccessControlAdapter(AccessControlService):
    async def assert_upload_allowed(self, actor_id: str) -> None:
        if not actor_id.strip():
            raise ForbiddenError("unauthenticated actor")

    async def assert_publish_allowed(self, actor_id: str, owner_id: str) -> None:
        if actor_id != owner_id:
            raise ForbiddenError("only owners can publish versions")

    async def assert_download_allowed(self, actor_id: str, owner_id: str, published: bool) -> None:
        if published:
            return
        if actor_id != owner_id:
            raise ForbiddenError("private versions are owner-only")

    async def assert_delete_allowed(self, actor_id: str, owner_id: str) -> None:
        if actor_id != owner_id:
            raise ForbiddenError("only owners can delete software")

