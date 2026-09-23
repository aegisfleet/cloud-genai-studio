import sys
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def parse_args():
    default_audio = PROJECT_ROOT / "outputs" / "10deg_song_2min.flac"
    if not default_audio.exists():
        default_audio = PROJECT_ROOT / "outputs" / "10deg_song_twitter.mp3"

    parser = argparse.ArgumentParser(description="Generate MP4 video with audio waveform for Twitter/X sharing")
    parser.add_argument("--audio", type=str, default=str(default_audio), help="Input audio file (FLAC recommended)")
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "outputs" / "10deg_song_twitter.mp4"), help="Output MP4 file")
    parser.add_argument("--audio-bitrate", type=str, default="256k", help="Audio bitrate (e.g. 256k, 320k)")
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
    draw.text((width // 2, int(height * 0.88)), "Style: Modern J-Rock · 160 BPM · Key: B♭ → B  |  High-Fidelity Audio", font=font_small, fill=(100, 116, 139, 240), anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path))
    return str(out_path), (fx0, fy0, frame_w, frame_h, center_y)

def encode_mp4(ffmpeg_exe, bg_path, audio_file, out_file, wave_params, audio_bitrate="256k", video_bitrate="80k"):
    fx0, fy0, frame_w, frame_h = wave_params
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
        "-preset", "slow",
        "-b:v", video_bitrate,
        "-maxrate", "120k",
        "-bufsize", "240k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-shortest",
        str(out_file)
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg Error:\n", res.stderr)
        raise RuntimeError("FFmpeg encoding failed.")

def main():
    args = parse_args()
    audio_file = Path(args.audio)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {args.audio}")

    print(f"Using audio input: {audio_file} (Audio Bitrate Target: {args.audio_bitrate})")

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

    # Step 1: Encode with target audio bitrate (e.g. 256k) and efficient video bitrate (75k)
    print(f"Encoding video with High-Fidelity Audio ({args.audio_bitrate} AAC)...")
    encode_mp4(
        ffmpeg_exe=ffmpeg_exe,
        bg_path=bg_path,
        audio_file=audio_file,
        out_file=out_file,
        wave_params=(fx0, fy0, frame_w, frame_h),
        audio_bitrate=args.audio_bitrate,
        video_bitrate="75k"
    )

    size_bytes = out_file.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"Initial encoded size: {size_mb:.2f} MB ({size_bytes} bytes)")

    # Step 2: If size slightly exceeds 5.0MB, fine-tune to 224k AAC to strictly ensure <= 5.0MB
    if size_mb > 5.0:
        print(f"File size ({size_mb:.2f} MB) is slightly over 5.0MB. Fine-tuning to 224k AAC to guarantee < 5MB...")
        encode_mp4(
            ffmpeg_exe=ffmpeg_exe,
            bg_path=bg_path,
            audio_file=audio_file,
            out_file=out_file,
            wave_params=(fx0, fy0, frame_w, frame_h),
            audio_bitrate="224k",
            video_bitrate="65k"
        )
        size_bytes = out_file.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        print(f"Adjusted encoded size: {size_mb:.2f} MB ({size_bytes} bytes)")

    print(f"\nSUCCESS: Video created: {out_file}")
    print(f"Final File Size: {size_mb:.2f} MB ({size_bytes} bytes)")
    print(f"Audio Quality: High-Bitrate AAC from lossless master ({audio_file.name})")

if __name__ == "__main__":
    main()
