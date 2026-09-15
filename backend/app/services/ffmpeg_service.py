import os
import subprocess
import json
from app.config import FFMPEG_PATH, FFPROBE_PATH

# Formatos aceitos como destino na conversão
SUPPORTED_FORMATS = ["mp3", "wav", "ogg", "flac", "m4a"]

# Taxas de bits aceitas na redução
SUPPORTED_BITRATES = ["32k", "64k", "96k", "128k"]


def get_processed_path(folder_path: str, ext: str) -> str:
    return os.path.join(folder_path, f"audio_processed.{ext}")


def get_output_ext(processing_type: str, original_ext: str, target_format: str | None = None) -> str:
    """Decide a extensão do arquivo processado."""
    if processing_type == "convert":
        if target_format not in SUPPORTED_FORMATS:
            raise ValueError(f"Formato de destino inválido. Use um destes: {', '.join(SUPPORTED_FORMATS)}.")
        return target_format

    if processing_type == "bitrate" and original_ext not in ["mp3", "m4a"]:
        return "mp3"

    return original_ext


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
    sample_rate: int | None = None,
) -> None:
    """Executa o FFmpeg de acordo com o tipo de processamento e parâmetros opcionais."""

    if processing_type == "normalize":
        args = ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(sample_rate or 44100)]
    elif processing_type == "mono":
        args = ["-ac", "1"]
    elif processing_type == "speed":
        factor = speed_factor or 1.5
        if factor < 0.5 or factor > 2.0:
            raise ValueError("A velocidade deve ficar entre 0.5 e 2.0.")
        args = ["-af", f"atempo={factor}"]
    elif processing_type == "bitrate":
        bitrate = target_bitrate or "64k"
        if bitrate not in SUPPORTED_BITRATES:
            raise ValueError(f"Taxa de bits inválida. Use uma destas: {', '.join(SUPPORTED_BITRATES)}.")
        args = ["-b:a", bitrate]
    elif processing_type == "convert":
        args = []  # o FFmpeg escolhe o codificador pela extensão do output_path
    else:
        raise ValueError(f"Tipo de processamento inválido: {processing_type}")

    cmd = [FFMPEG_PATH, "-y", "-i", input_path, "-vn", *args, output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Erro no FFmpeg: {result.stderr}")
