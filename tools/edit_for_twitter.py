import os
import sys
import argparse
from pathlib import Path
import numpy as np
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def parse_args():
    parser = argparse.ArgumentParser(description="Trim and fade out audio for Twitter/X sharing")
    parser.add_argument("--input", type=str, default=str(PROJECT_ROOT / "outputs" / "10deg_song.flac"), help="Input audio file")
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "outputs" / "10deg_song_twitter.mp3"), help="Output MP3 file")
    parser.add_argument("--duration", type=float, default=120.0, help="Target duration in seconds (default: 120)")
    parser.add_argument("--fade", type=float, default=5.0, help="Fadeout duration in seconds (default: 5.0)")
    return parser.parse_args()

def main():
    args = parse_args()
    input_file = Path(args.input)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    print(f"Loading {input_file}...")
    data, sr = sf.read(str(input_file))
    total_samples = len(data)
    duration = total_samples / sr
    print(f"Sample Rate: {sr} Hz, Channels: {data.ndim}, Original Duration: {duration:.2f}s")

    target_samples = int(args.duration * sr)
    fade_samples = int(args.fade * sr)

    if total_samples > target_samples:
        trimmed = data[:target_samples].copy()
    else:
        trimmed = data.copy()
        fade_samples = min(fade_samples, len(trimmed))

    # Apply smooth cosine fadeout to the last fade_samples
    fade_curve = 0.5 * (1.0 + np.cos(np.linspace(0.0, np.pi, fade_samples)))
    if trimmed.ndim == 2:
        fade_curve = fade_curve[:, np.newaxis]

    trimmed[-fade_samples:] *= fade_curve

    out_mp3 = Path(args.output)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    print(f"Exporting MP3 to {out_mp3}...")

    try:
        sf.write(str(out_mp3), trimmed, sr, format="MP3")
    except Exception as e:
        print(f"Direct MP3 write failed ({e}), trying fallback to OGG...")
        out_ogg = out_mp3.with_suffix(".ogg")
        sf.write(str(out_ogg), trimmed, sr, format="OGG")
        print(f"Exported OGG to {out_ogg}")

    if out_mp3.exists():
        size_mb = out_mp3.stat().st_size / (1024 * 1024)
        print(f"MP3 Size: {size_mb:.2f} MB ({out_mp3.stat().st_size} bytes)")
        if size_mb <= 5.0:
            print("SUCCESS: File size is under 5MB threshold!")
        else:
            print("WARNING: File size exceeds 5MB.")

    # Also save 2-min trimmed FLAC for archival
    out_flac = out_mp3.with_name(f"{out_mp3.stem}_2min.flac")
    sf.write(str(out_flac), trimmed, sr, format="FLAC")
    flac_size_mb = out_flac.stat().st_size / (1024 * 1024)
    print(f"Archival 2-min FLAC Size: {flac_size_mb:.2f} MB ({out_flac})")

if __name__ == "__main__":
    main()
