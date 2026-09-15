import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Audio

router = APIRouter()


@router.get("/audio/{audio_id}/{kind}")
def get_audio_file(audio_id: uuid.UUID, kind: str, db: Session = Depends(get_db)):
    audio = db.query(Audio).filter(Audio.id == audio_id).first()
    if audio is None:
        raise HTTPException(status_code=404, detail="Áudio não encontrado.")

    if kind == "original":
        path = audio.path_original
    elif kind == "processed":
        path = audio.path_processed
    else:
        raise HTTPException(status_code=404, detail="Use original ou processed no endereço.")

    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor.")

    return FileResponse(path)
