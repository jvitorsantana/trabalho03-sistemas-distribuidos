import os
import subprocess

def get_processed_path(folder_path: str, ext: str) -> str:
    """Retorna o caminho onde o arquivo processado deve ser salvo."""
    return os.path.join(folder_path, f"audio_processed.{ext}")


def process_audio(input_path: str, output_path: str, processing_type: str) -> None:
    """Executa o FFmpeg de acordo com o tipo de processamento escolhido."""

    commands = {
        "normalize": ["-af", "loudnorm"],
        "mono": ["-ac", "1"],
        "speed": ["-af", "atempo=1.5"],
        "bitrate": ["-b:a", "64k"],
    }

    if processing_type == "convert":
        # Conversão de formato: apenas troca o container/codec, sem filtro extra
        args = []
    elif processing_type in commands:
        args = commands[processing_type]
    else:
        raise ValueError(f"Tipo de processamento inválido: {processing_type}")

    cmd = ["ffmpeg", "-y", "-i", input_path, *args, output_path]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Erro no FFmpeg: {result.stderr}")