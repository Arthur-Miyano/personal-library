from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class FontResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    filename: str
    stored_path: str
    font_family: str
    file_size: int
    created_at: datetime
