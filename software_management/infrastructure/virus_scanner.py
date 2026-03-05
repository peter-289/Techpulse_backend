from __future__ import annotations

from typing import AsyncIterable, AsyncIterator

from software_management.application.errors import ValidationError
from software_management.application.interfaces import VirusScannerService


class AsyncVirusScannerAdapter(VirusScannerService):
    """Simple async scanner adapter that can be replaced with ClamAV or SaaS scanners."""

    _SIGNATURE = b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"

    def wrap_stream(
        self,
        stream: AsyncIterable[bytes],
        *,
        file_name: str,
        content_type: str,
    ) -> AsyncIterable[bytes]:
        async def _scan() -> AsyncIterator[bytes]:
            carry = b""
            async for chunk in stream:
                if not chunk:
                    continue
                payload = carry + chunk
                if self._SIGNATURE in payload:
                    raise ValidationError("virus signature detected")
                carry = payload[-(len(self._SIGNATURE) - 1) :]
                yield chunk

        return _scan()

