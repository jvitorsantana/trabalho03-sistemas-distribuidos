import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Audio
from app.services import ffmpeg_service

router = APIRouter()


def get_file_path(audio_id: uuid.UUID, kind: str, db: Session) -> str:
  audio = db.query(Audio).filter(Audio.id == audio_id).first()
  if audio is None:
      raise HTTPException(status_code=404, detail="Áudio não encontrado.")

  if kind == "original":
    path = audio.path_original
  elif kind == "processed":
    path = audio.path_processed
  elif kind == "waveform":
    path = os.path.join(os.path.dirname(audio.path_original), "waveform.png")
  else:
    raise HTTPException(status_code=404, detail="Use original, processed ou waveform no endereço.")

  if not path or not os.path.isfile(path):
    raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor.")

  return path


@router.get("/audio/{audio_id}/info/{kind}")
def get_audio_details(audio_id: uuid.UUID, kind: str, db: Session = Depends(get_db)):
  if kind not in ["original", "processed"]:
    raise HTTPException(status_code=404, detail="Use original ou processed no endereço.")

  path = get_file_path(audio_id, kind, db)
  info = ffmpeg_service.get_audio_info(path)
  info["ext"] = path.rsplit(".", 1)[-1]
  info["size_bytes"] = os.path.getsize(path)
  return info


@router.get("/audio/{audio_id}/{kind}")
def get_audio_file(audio_id: uuid.UUID, kind: str, db: Session = Depends(get_db)):
  path = get_file_path(audio_id, kind, db)
  return FileResponse(path)
