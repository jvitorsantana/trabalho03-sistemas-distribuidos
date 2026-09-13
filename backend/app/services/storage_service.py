import os
import json
import uuid
from datetime import datetime
from app.config import STORAGE_DIR


def create_audio_folder() -> tuple[str, str]:
    """Cria a subpasta storage/YYYY-MM-DD/<uuid>/ e retorna (audio_id, caminho da pasta)."""
    audio_id = str(uuid.uuid4())
    date_folder = datetime.utcnow().strftime("%Y-%m-%d")
    folder_path = os.path.join(STORAGE_DIR, date_folder, audio_id)
    os.makedirs(folder_path, exist_ok=True)
    return audio_id, folder_path


def save_original_file(folder_path: str, file_bytes: bytes, ext: str) -> str:
    """Salva o arquivo original como audio.{ext} e retorna o caminho completo."""
    file_path = os.path.join(folder_path, f"audio.{ext}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return file_path


def save_meta_json(folder_path: str, meta: dict) -> str:
    """Salva o meta.json com informações complementares."""
    meta_path = os.path.join(folder_path, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4, ensure_ascii=False)
    return meta_path


def move_to_trash(folder_path: str) -> str:
    """Move a pasta inteira de um áudio para storage/trash/."""
    trash_dir = os.path.join(STORAGE_DIR, "trash")
    os.makedirs(trash_dir, exist_ok=True)
    folder_name = os.path.basename(folder_path)
    destination = os.path.join(trash_dir, folder_name)
    os.rename(folder_path, destination)
    return destination