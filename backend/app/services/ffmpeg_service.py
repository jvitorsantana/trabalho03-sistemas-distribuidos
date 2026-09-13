import os
import subprocess
import json
from app.config import FFMPEG_PATH, FFPROBE_PATH


def get_processed_path(folder_path: str, ext: str) -> str:
    return os.path.join(folder_path, f"audio_processed.{ext}")

def get_audio_info(file_path: str) -> dict:
    """Usa ffprobe para extrair duração, sample_rate, canais e bitrate do áudio."""
    cmd = [
        FFPROBE_PATH, "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Erro no ffprobe: {result.stderr}")

    data = json.loads(result.stdout)
    stream = data["streams"][0]
    fmt = data["format"]

    return {
        "duration_sec": float(fmt.get("duration", 0)),
        "sample_rate": int(stream.get("sample_rate", 0)),
        "channels": int(stream.get("channels", 0)),
        "bitrate": int(fmt.get("bit_rate", 0)),
    }

def process_audio(
    input_path: str,
    output_path: str,
    processing_type: str,
    speed_factor: float | None = None,
    target_bitrate: str | None = None,
) -> None:
    """Executa o FFmpeg de acordo com o tipo de processamento e parâmetros opcionais."""

    if processing_type == "normalize":
        args = ["-af", "loudnorm"]
    elif processing_type == "mono":
        args = ["-ac", "1"]
    elif processing_type == "speed":
        factor = speed_factor or 1.5
        args = ["-af", f"atempo={factor}"]
    elif processing_type == "bitrate":
        bitrate = target_bitrate or "64k"
        args = ["-b:a", bitrate]
    elif processing_type == "convert":
        args = []  # conversão só pela extensão do output_path
    else:
        raise ValueError(f"Tipo de processamento inválido: {processing_type}")

    cmd = [FFMPEG_PATH, "-y", "-i", input_path, *args, output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Erro no FFmpeg: {result.stderr}")