# Pydantic Schemas for IO Validation
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UploadResponse(BaseModel):
    message: str
    fingerprint: Optional[str] = None

class MatchResult(BaseModel):
    matches: List[str]
    confidence: Optional[float] = None  # For future use with actual matching

class AudioBase(BaseModel):
    filename: str
    file_type: str
    size: int
    created_at: datetime

class AudioCreate(AudioBase):
    pass

class Audio(AudioBase):
    id: int
    file_path: str

    class Config:
        from_attributes = True