import sys
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def parse_args():
    parser = argparse.ArgumentParser(description="Generate MP4 video with audio waveform for Twitter/X sharing")
    parser.add_argument("--audio", type=str, default=str(PROJECT_ROOT / "outputs" / "10deg_song_twitter.mp3"), help="Input audio file")
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "outputs" / "10deg_song_twitter.mp4"), help="Output MP4 file")
    parser.add_argument("--title", type=str, default="10 ℃", help="Track title")
    parser.add_argument("--subtitle", type=str, default="しゃろう「10℃」- J-Rock Arrangement -", help="Track subtitle")
    parser.add_argument("--credits", type=str, default="Original: しゃろう (Sharou)  |  Arrangement & AI Vocal: YuE2 (L4 GPU)  |  Transcription: SheetSage2", help="Credits line")
    parser.add_argument("--tag", type=str, default="FAN-MADE ARRANGE", help="Chip tag")
    return parser.parse_args()

def create_background(title, subtitle, credits_text, tag_text, width=1280, height=720, out_path=None):
    if out_path is None:
        out_path = PROJECT_ROOT / "outputs" / "bg.png"
    else:
        out_path = Path(out_path)

    img = Image.new("RGBA", (width, height), (13, 17, 26, 255))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        r = int(11 + (y / height) * 8)
        g = int(15 + (y / height) * 11)
        b = int(25 + (y / height) * 15)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    font_paths = [
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    font_large, font_sub, font_small, font_tag = None, None, None, None

    for fp in font_paths:
        if Path(fp).exists():
            try:
                font_large = ImageFont.truetype(fp, 56)
                font_sub = ImageFont.truetype(fp, 26)
                font_small = ImageFont.truetype(fp, 18)
                font_tag = ImageFont.truetype(fp, 15)
                break
            except Exception:
                continue

    if font_large is None:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    # Category Tag / Chip
    chip_w, chip_h = 160, 28
    chip_x, chip_y = (width - chip_w) // 2, int(height * 0.15)
    draw.rounded_rectangle([chip_x, chip_y, chip_x + chip_w, chip_y + chip_h], radius=14, fill=(30, 41, 59, 255), outline=(56, 189, 248, 180), width=1)
    draw.text((width // 2, chip_y + chip_h // 2), tag_text, font=font_tag, fill=(56, 189, 248, 255), anchor="mm")

    # Main Title
    draw.text((width // 2, int(height * 0.25)), title, font=font_large, fill=(255, 255, 255, 255), anchor="mm")

    # Subtitle
    draw.text((width // 2, int(height * 0.34)), subtitle, font=font_sub, fill=(203, 213, 225, 255), anchor="mm")

    # Credit details
    draw.text((width // 2, int(height * 0.41)), credits_text, font=font_small, fill=(148, 163, 184, 255), anchor="mm")

    # Clean Waveform Frame Container (Center)
    center_y = int(height * 0.62)
    frame_w, frame_h = 920, 160
    fx0, fy0 = (width - frame_w) // 2, center_y - frame_h // 2
    fx1, fy1 = fx0 + frame_w, fy0 + frame_h

    draw.rounded_rectangle([fx0, fy0, fx1, fy1], radius=8, fill=(19, 26, 41, 255), outline=(51, 65, 85, 255), width=1)
    draw.line([(fx0 + 10, center_y), (fx1 - 10, center_y)], fill=(30, 41, 59, 255), width=1)

    # Footer track specs
    draw.text((width // 2, int(height * 0.88)), "Style: Modern J-Rock · 160 BPM · Key: B♭ → B  |  Short Version (2:00)", font=font_small, fill=(100, 116, 139, 240), anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path))
    print(f"Clean background image created: {out_path}")
    return str(out_path), (fx0, fy0, frame_w, frame_h, center_y)

def main():
    args = parse_args()
    audio_file = Path(args.audio)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {args.audio}")

    bg_path, (fx0, fy0, frame_w, frame_h, center_y) = create_background(
        title=args.title,
        subtitle=args.subtitle,
        credits_text=args.credits,
        tag_text=args.tag
    )
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    out_file = Path(args.output)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    if out_file.exists():
        out_file.unlink()

    print("Encoding video with visible, solid waveform (compression-resistant)...")

    wave_w = frame_w - 24
    wave_h = frame_h - 24
    wave_x = fx0 + 12
    wave_y = fy0 + 12

    cmd = [
        ffmpeg_exe, "-y",
        "-loop", "1", "-i", bg_path,
        "-i", str(audio_file),
        "-filter_complex",
        f"[1:a]showwaves=s={wave_w}x{wave_h}:mode=cline:colors=0x38bdf8:scale=sqrt:r=30,format=rgba[waves];"
        f"[0:v][waves]overlay=x={wave_x}:y={wave_y}:shortest=1[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-b:v", "230k",
        "-maxrate", "270k",
        "-bufsize", "540k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "96k",
        "-shortest",
        str(out_file)
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg Error:\n", res.stderr)
        raise RuntimeError("FFmpeg encoding failed.")

    size_bytes = out_file.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"Video created: {out_file}")
    print(f"Video File Size: {size_mb:.2f} MB ({size_bytes} bytes)")
    if size_mb <= 5.0:
        print("SUCCESS: MP4 size is under 5MB threshold!")

if __name__ == "__main__":
    main()
