import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path


class InvalidVideo(ValueError):
    pass


class InspectionUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class VideoInfo:
    duration_seconds: float
    codec: str


def inspect_video(path: Path, content_type: str) -> VideoInfo:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe",
             "-select_streams", "v:0", "-show_entries",
             "stream=codec_name:format=duration,format_name", "-of", "json", str(path)],
            capture_output=True, text=True, timeout=15, check=False,
        )
    except FileNotFoundError as exc:
        raise InspectionUnavailable("ffprobe não está instalado no servidor") from exc
    except subprocess.TimeoutExpired as exc:
        raise InvalidVideo("Tempo limite excedido ao inspecionar vídeo") from exc
    try:
        if result.returncode != 0:
            raise ValueError()
        data = json.loads(result.stdout)
        codec = data["streams"][0]["codec_name"]
        duration = float(data["format"]["duration"])
        container = data["format"]["format_name"]
        valid = (
            content_type == "video/mp4" and "mp4" in container and codec == "h264"
        ) or (
            content_type == "video/webm" and "webm" in container and codec in {"vp8", "vp9"}
        )
        if not valid or not math.isfinite(duration) or duration <= 0:
            raise ValueError()
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise InvalidVideo("Vídeo inválido; use MP4/H.264 ou WebM/VP8/VP9") from exc
    return VideoInfo(duration_seconds=duration, codec=codec)
