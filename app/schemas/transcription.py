from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TranscriptionRead(BaseModel):
    id: int
    user_id: int
    original_filename: str
    transcript_text: str
    status: str
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

