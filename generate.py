import os
import sys
import json
import argparse
from pathlib import Path
import torch

def parse_args():
    parser = argparse.ArgumentParser(description="Generate music with YuE2 (Google Cloud NVIDIA L4 optimized)")
    parser.add_argument("--style", type=str, default="J-Pop, emotional female vocal, dynamic piano, upbeat anime opening", help="Style / genre tags")
    parser.add_argument("--lyrics", type=str, default="", help="Lyrics with section tags, e.g. [verse], [chorus]")
    parser.add_argument("--lyrics-file", type=str, default=None, help="Path to text file containing lyrics")
    parser.add_argument("--cot", type=str, choices=["full", "melody", "off"], default="full", help="CoT mode")
    parser.add_argument("--abc-file", type=str, default=None, help="Path to reference ABC notation file (.abc)")
    parser.add_argument("--ode-steps", type=int, default=32, help="ODE steps for audio synthesis (default: 32)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--output", type=str, default="outputs/song.flac", help="Output audio file path (.flac or .wav)")
    return parser.parse_args()

SAMPLE_LYRICS = """[verse]
朝の光が 街を包み込む
新しい一日が 今日も始まる
少しの不安と 大きな希望を
胸に抱いて 歩き出そう

[chorus]
風に乗せて 届けたいメロディ
どんな壁も 越えてゆけるから
信じた夢は 決して消えない
未来へ続く この空の下で
"""

def main():
    args = parse_args()
    lyrics = args.lyrics
    if args.lyrics_file and Path(args.lyrics_file).exists():
        lyrics = Path(args.lyrics_file).read_text(encoding="utf-8-sig")
    elif not lyrics.strip():
        lyrics = SAMPLE_LYRICS

    print("========================================")
    print("YuE2 CLI Music Generation")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"Style: {args.style}")
    print(f"CoT Mode: {args.cot}")
    print(f"ABC File: {args.abc_file}")
    print(f"Seed: {args.seed}")
    print(f"Output: {args.output}")
    print("----------------------------------------")
    print("Lyrics Preview:")
    print(lyrics.strip()[:150] + "...")
    print("========================================")

    ref_abc = None
    if args.abc_file and Path(args.abc_file).exists():
        ref_abc = Path(args.abc_file).read_text(encoding="utf-8").strip()
        print(f"Loaded reference ABC score from: {args.abc_file}")

    from yue2 import YuE2Pipeline
    from yue2.protocol import GenerationConfig

    gen_config = GenerationConfig(ode_steps=args.ode_steps)

    print("\nLoading YuE2 Pipeline (NVIDIA L4 24GB Optimized)...")
    pipe = YuE2Pipeline.from_pretrained(
        "m-a-p/YuE2-3B",
        vae="m-a-p/YuE2-Vae",
        device="cuda" if torch.cuda.is_available() else "cpu",
        backend="torch",
        offload_ar=False,
        vae_core_frames=1024,
        generation_config=gen_config,
        progress=True
    )

    print("\nGenerating song...")
    song = pipe(
        style=args.style,
        lyrics=lyrics,
        cot=args.cot,
        abc=ref_abc,
        seed=args.seed
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    saved_path = song.save(str(out_path))
    print(f"\nSong generated and saved to: {saved_path}")

    # Also save ABC score if generated
    if song.abc:
        abc_path = out_path.with_suffix(".abc")
        abc_path.write_text(song.abc, encoding="utf-8")
        print(f"Score saved to: {abc_path}")

if __name__ == "__main__":
    main()
