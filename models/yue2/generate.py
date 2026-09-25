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
    parser.add_argument("--vae", type=str, default="m-a-p/YuE2-Vae", help="Hugging Face repo or local path for VAE model")
    parser.add_argument("--ode-steps", type=int, default=32, help="ODE steps for audio synthesis (default: 32)")
    parser.add_argument("--temperature", type=float, default=1.0, help="Sampling temperature for audio semantic tokens (default: 1.0)")
    parser.add_argument("--top-p", type=float, default=0.95, help="Sampling top-p for audio semantic tokens (default: 0.95)")
    parser.add_argument("--cfg-scale", type=float, default=None, help="Classifier-Free Guidance scale (default: None / 1.0)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--output", type=str, default="outputs/song.flac", help="Output audio file path (.flac or .wav)")
    parser.add_argument("--backend", type=str, choices=["torch", "torch-eager", "vllm"], default="torch", help="PyTorch backend engine (default: torch, use torch-eager for RTX 3060 / Windows)")
    parser.add_argument("--offload-ar", action="store_true", help="Enable CPU offload for AR model to save VRAM on 12GB GPUs")
    parser.add_argument("--vae-core-frames", type=int, default=1024, help="VAE tile frame count (1024 for 24GB, 512 for 12GB)")
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

    print(f"\nLoading YuE2 Pipeline (backend={args.backend}, offload_ar={args.offload_ar}, vae_core_frames={args.vae_core_frames})...")
    pipe = YuE2Pipeline.from_pretrained(
        "m-a-p/YuE2-3B",
        vae=args.vae,
        device="cuda" if torch.cuda.is_available() else "cpu",
        backend=args.backend,
        offload_ar=args.offload_ar,
        vae_core_frames=args.vae_core_frames,
        generation_config=gen_config,
        progress=True
    )

    sampling_overrides = {}
    if args.temperature is not None:
        sampling_overrides["temperature"] = args.temperature
    if args.top_p is not None:
        sampling_overrides["top_p"] = args.top_p

    pipe_kwargs = {
        "style": args.style,
        "lyrics": lyrics,
        "cot": args.cot,
        "abc": ref_abc,
        "seed": args.seed,
    }
    if sampling_overrides:
        pipe_kwargs["semantic_sampling"] = sampling_overrides
    if args.cfg_scale is not None:
        pipe_kwargs["cfg_scale"] = args.cfg_scale

    print(f"Sampling: temp={args.temperature}, top_p={args.top_p}")
    if args.cfg_scale is not None:
        print(f"CFG Guidance Scale: {args.cfg_scale}")

    print("\nGenerating song...")
    song = pipe(**pipe_kwargs)

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
