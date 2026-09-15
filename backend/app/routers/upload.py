import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Audio, AudioResponse
from app.services import storage_service, ffmpeg_service, waveform_service

router = APIRouter()


@router.post("/upload", response_model=AudioResponse)
async def upload_audio(
    file: UploadFile = File(...),
    processing_type: str = Form(...),
    speed_factor: float | None = Form(None),
    target_bitrate: str | None = Form(None),
    target_format: str | None = Form(None),
    db: Session = Depends(get_db),
):
    original_ext = file.filename.split(".")[-1].lower()
    file_bytes = await file.read()

    # 1. Cria a pasta organizada por data/UUID
    audio_id, folder_path = storage_service.create_audio_folder()

    # 2. Salva o arquivo original
    path_original = storage_service.save_original_file(folder_path, file_bytes, original_ext)

    try:
        audio_info = ffmpeg_service.get_audio_info(path_original)

        # 3. Processa com FFmpeg
        output_ext = ffmpeg_service.get_output_ext(processing_type, original_ext, target_format)
        path_processed = ffmpeg_service.get_processed_path(folder_path, output_ext)
        ffmpeg_service.process_audio(
            path_original, path_processed, processing_type,
            speed_factor=speed_factor, target_bitrate=target_bitrate,
            sample_rate=audio_info["sample_rate"],
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail="FFmpeg/ffprobe não está instalado ou não está no PATH do sistema.",
        ) from e
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Gera o waveform a partir do original
    waveform_service.generate_waveform(path_original, folder_path)

    # 5. Salva meta.json complementar
    storage_service.save_meta_json(folder_path, {
        "processing_type": processing_type,
        "speed_factor": speed_factor,
        "target_bitrate": target_bitrate,
        "target_format": target_format,
        "output_ext": output_ext,
    })

    # 6. Registra no banco
    audio = Audio(
        id=audio_id,
        original_name=file.filename,
        original_ext=original_ext,
        mime_type=file.content_type,
        size_bytes=len(file_bytes),
        duration_sec=audio_info["duration_sec"],
        sample_rate=audio_info["sample_rate"],
        channels=audio_info["channels"],
        bitrate=audio_info["bitrate"],
        processing_type=processing_type,
        path_original=path_original,
        path_processed=path_processed,
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)

    return audio
