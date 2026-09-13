import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")


def _find_media_tool(name: str) -> str:
	configured_path = os.getenv(name.upper() + "_PATH")
	if configured_path and os.path.isfile(configured_path):
		return configured_path

	system_path = shutil.which(name)
	if system_path:
		return system_path

	winget_root = Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
	matches = sorted(winget_root.glob(f"Gyan.FFmpeg.*/*/bin/{name}.exe"))
	if matches:
		return str(matches[-1])

	return name


FFMPEG_PATH = _find_media_tool("ffmpeg")
FFPROBE_PATH = _find_media_tool("ffprobe")