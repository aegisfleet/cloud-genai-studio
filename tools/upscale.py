#!/usr/bin/env python3
"""Video upscaler to 1080p using high-quality Lanczos filtering and H.264 encoding."""

import argparse
import subprocess
import sys
from pathlib import Path
import imageio_ffmpeg


def upscale_video(input_path: str, output_path: str, target_width: int = 1920, target_height: int = 1080):
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # High-quality Lanczos scaling with sharp bicubic/lanczos filtering
    # Aspect ratio preserving scale & pad or direct fit
    filter_complex = f"scale={target_width}:{target_height}:flags=lanczos+accurate_rnd"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_file),
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-c:a", "copy",
        str(output_file)
    ]

    print(f"Upscaling '{input_file.name}' -> '{output_file.name}' ({target_width}x{target_height})...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"Successfully created: {output_file} ({output_file.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upscale video to 1080p")
    parser.add_argument("input", help="Path to input video")
    parser.add_argument("output", help="Path to output 1080p video")
    parser.add_argument("--width", type=int, default=1920, help="Target width")
    parser.add_argument("--height", type=int, default=1080, help="Target height")
    args = parser.parse_args()

    upscale_video(args.input, args.output, args.width, args.height)
