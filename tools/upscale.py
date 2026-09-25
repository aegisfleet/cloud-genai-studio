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


def upscale_image(input_path: str, output_path: str, target_width: int = 2048, target_height: int = 2048):
    from PIL import Image
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Upscaling Image '{input_file.name}' -> '{output_file.name}' ({target_width}x{target_height}) using High-Precision Lanczos...")
    with Image.open(input_file) as img:
        upscaled = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        upscaled.save(output_file)

    print(f"Successfully created: {output_file} ({output_file.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upscale image or video to high resolution (Lanczos / FFmpeg)")
    parser.add_argument("input", help="Path to input image or video")
    parser.add_argument("output", help="Path to output upscaled file")
    parser.add_argument("--width", type=int, default=2048, help="Target width (default: 2048)")
    parser.add_argument("--height", type=int, default=2048, help="Target height (default: 2048)")
    args = parser.parse_args()

    in_ext = Path(args.input).suffix.lower()
    if in_ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        upscale_image(args.input, args.output, args.width, args.height)
    else:
        upscale_video(args.input, args.output, args.width, args.height)
