#!/usr/bin/env python3
"""
Qwen-Image 2.1 画風別（アニメ調・リアル調・水彩調・シネマティック調）実機検証スクリプト
"""

import argparse
import os
import sys
import time
import torch
from PIL import Image

STYLES = [
    {
        "id": "01_anime_cel",
        "name": "アニメ調 (Anime / Cel-Shaded)",
        "style_prefix": "Japanese modern anime illustration, clean crisp line art, vibrant cel-shaded coloring, 2D anime aesthetic, Kyoto Animation and Makoto Shinkai visual style, expressive large anime eyes, smooth color gradients, masterpiece digital illustration",
        "style_negative": "photorealistic, realistic human skin texture, pores, 3d render, live action, real life photography, western cartoon, plastic 3d",
        "cfg": 5.0,
    },
    {
        "id": "02_realistic_photo",
        "name": "リアル写真調 (Hyperrealistic Raw Photo)",
        "style_prefix": "Hyperrealistic raw photographic portrait, shot on 35mm lens, f/1.8 aperture, authentic natural skin texture with subtle pores and imperfections, soft volumetric natural lighting, shallow depth of field, unedited DSLR photo, 8k resolution, Kodak Portra film aesthetic",
        "style_negative": "anime, illustration, drawing, painting, 3d render, CGI, cartoon, airbrushed, plastic smooth skin, oversaturated videogame graphic",
        "cfg": 3.5,
    },
    {
        "id": "03_watercolor",
        "name": "水彩画調 (Traditional Watercolor)",
        "style_prefix": "Traditional watercolor painting on cold-press textured paper, visible bleeding paint edges, soft pastel color washes, hand-drawn organic brush strokes, artisanal fine art, translucent delicate watercolor pigments, splashing water droplets",
        "style_negative": "photorealistic, 3d render, digital vector, sharp harsh digital lines, computer graphics, glossy plastic",
        "cfg": 4.5,
    },
    {
        "id": "04_cinematic_movie",
        "name": "シネマティック映画調 (Cinematic Film Still)",
        "style_prefix": "Cinematic movie still, 35mm anamorphic lens, dramatic chiaroscuro volumetric lighting, subtle 35mm film grain, muted cinematic color grading, atmospheric rim light, Panavision film aesthetic, award-winning cinematography",
        "style_negative": "cartoon, anime, 3d render, plastic, oversaturated, amateur snapshot",
        "cfg": 4.0,
    },
]

SUBJECTS = [
    {
        "id": "cyberpunk_girl",
        "prompt": "A young girl standing in a rainy Neo-Tokyo alleyway at night, surrounded by glowing neon signs and umbrella reflections on wet pavement",
    },
    {
        "id": "sakura_student",
        "prompt": "A Japanese high school student holding a vintage book under blooming cherry blossom trees with falling petals in gentle spring breeze",
    }
]

def main():
    parser = argparse.ArgumentParser(description="Qwen-Image 2.1 Style Comparison")
    parser.add_argument("--output_dir", type=str, default="outputs/style_comparison", help="Output directory")
    parser.add_argument("--steps", type=int, default=15, help="Sampling steps")
    parser.add_argument("--width", type=int, default=1024, help="Width")
    parser.add_argument("--height", type=int, default=1024, help="Height")
    parser.add_argument("--seed", type=int, default=123, help="Base seed")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 70)
    print(" Qwen-Image 2.1 画風別スタイル比較検証 (アニメ調 / リアル調 / 水彩 / 映画)")
    print(f" Resolution: {args.width}x{args.height}, Steps: {args.steps}")
    print("=" * 70)

    from diffusers import DiffusionPipeline

    print(">>> Loading Qwen-Image 2.1 in BF16...")
    load_start = time.time()
    pipe = DiffusionPipeline.from_pretrained(
        "Qwen/Qwen-Image-2.1",
        torch_dtype=torch.bfloat16,
    )
    pipe.enable_model_cpu_offload()
    print(f">>> Model loaded successfully in {time.time() - load_start:.2f}s!")

    tasks = []
    for sub in SUBJECTS:
        for st in STYLES:
            tasks.append({
                "sub_id": sub["id"],
                "sub_prompt": sub["prompt"],
                "style_id": st["id"],
                "style_name": st["name"],
                "full_prompt": f"{st['style_prefix']}, {sub['prompt']}",
                "negative_prompt": st["style_negative"],
                "cfg": st["cfg"],
                "filename": f"{sub['id']}_{st['id']}.png"
            })

    print(f"Total generations: {len(tasks)}")
    print("-" * 70)

    results = []
    total_start = time.time()

    for idx, t in enumerate(tasks, 1):
        out_path = os.path.join(args.output_dir, t["filename"])
        print(f"\n[{idx}/{len(tasks)}] {t['sub_id']} x {t['style_name']}")
        print(f"Prompt: {t['full_prompt'][:100]}...")
        print(f"CFG: {t['cfg']}")

        if os.path.exists(out_path):
            size_kb = os.path.getsize(out_path) / 1024
            print(f">>> [SKIPPED] {out_path} already exists ({size_kb:.1f} KB)")
            results.append({"idx": idx, "task": t, "time": 0.0, "size_kb": size_kb, "skipped": True})
            continue

        generator = torch.Generator(device="cuda").manual_seed(args.seed)

        t_start = time.time()
        with torch.inference_mode():
            result = pipe(
                prompt=t["full_prompt"],
                negative_prompt=t["negative_prompt"],
                width=args.width,
                height=args.height,
                num_inference_steps=args.steps,
                true_cfg_scale=t["cfg"],
                generator=generator
            )
            image = result.images[0]

        gen_time = time.time() - t_start
        image.save(out_path)
        size_kb = os.path.getsize(out_path) / 1024

        print(f">>> Done in {gen_time:.2f}s ({size_kb:.1f} KB) -> {t['filename']}")
        results.append({"idx": idx, "task": t, "time": gen_time, "size_kb": size_kb, "skipped": False})

    print("\n" + "=" * 70)
    print(f" Style comparison batch completed in {time.time() - total_start:.2f}s!")
    print("=" * 70)

if __name__ == "__main__":
    main()
