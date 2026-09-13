import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
from app.database import Base


# ---------- Modelo SQLAlchemy (tabela do banco) ----------

class Audio(Base):
    __tablename__ = "audios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_name = Column(String, nullable=False)
    original_ext = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    duration_sec = Column(Float, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bitrate = Column(Integer, nullable=True)
    processing_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    path_original = Column(String, nullable=False)
    path_processed = Column(String, nullable=True)


# ---------- Schemas Pydantic (entrada/saída da API) ----------

class AudioResponse(BaseModel):
    id: uuid.UUID
    original_name: str
    original_ext: str
    mime_type: str | None
    size_bytes: int | None
    duration_sec: float | None
    sample_rate: int | None
    channels: int | None
    bitrate: int | None
    processing_type: str | None
    created_at: datetime
    path_original: str
    path_processed: str | None

    class Config:
        from_attributes = True