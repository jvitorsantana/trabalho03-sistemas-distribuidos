from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Audio, AudioResponse

router = APIRouter()

@router.get('/history', response_model=list[AudioResponse])
def list_history(db: Session = Depends(get_db)):
  audios = db.query(Audio).order_by(Audio.created_at.desc()).all()
  return audios