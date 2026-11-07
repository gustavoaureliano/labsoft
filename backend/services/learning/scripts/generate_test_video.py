"""Generate disposable real video fixtures; never invoked by the API."""

import argparse
import subprocess
from pathlib import Path


def generate_video(path: Path, *, duration: int = 12) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    codec = ["-c:v", "libvpx-vp9"] if path.suffix == ".webm" else ["-c:v", "libx264", "-movflags", "+faststart"]
    subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-n", "-f", "lavfi", "-i",
         "testsrc2=size=320x180:rate=10", "-t", str(duration), "-pix_fmt", "yuv420p",
         *codec, str(path)],
        check=True, timeout=60,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    generate_video(args.output)
