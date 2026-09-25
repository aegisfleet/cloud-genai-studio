#!/usr/bin/env python3
"""
Qwen-Image-2.1 Text-to-Image Generation & Multi-Approach Benchmark CLI
Supports:
  - Approach A: 2K Native Generation with Tiled VAE (Memory-Safe Chunked Decode)
  - Approach B: 2K Native Generation with bitsandbytes Quantization (INT8 / NF4)
  - Approach C: 1K Native Generation + High-Quality Lanczos/AI Super-Resolution to 2K
"""

import argparse
import os
import sys
import time
import psutil
import torch
from PIL import Image

def get_system_ram_gb():
    mem = psutil.virtual_memory()
    return mem.used / (1024 ** 3), mem.total / (1024 ** 3)

STYLE_PRESETS = {
    "anime": {
        "name": "アニメ調 (Anime / Cel-Shaded)",
        "prefix": "Japanese modern anime illustration, clean crisp line art, vibrant cel-shaded coloring, 2D anime aesthetic, Kyoto Animation visual style, expressive large anime eyes, smooth color gradients, masterpiece digital illustration",
        "negative": "photorealistic, realistic human skin texture, pores, 3d render, live action, real life photography, western cartoon, plastic 3d",
        "cfg": 5.0
    },
    "realistic": {
        "name": "リアル写真調 (Hyperrealistic Raw Photo)",
        "prefix": "Hyperrealistic raw photographic portrait, shot on 35mm lens, f/1.8 aperture, authentic natural skin texture with subtle pores and imperfections, soft volumetric natural lighting, shallow depth of field, unedited DSLR photo, 8k resolution, Kodak Portra film aesthetic",
        "negative": "anime, illustration, drawing, painting, 3d render, CGI, cartoon, airbrushed, plastic smooth skin, oversaturated videogame graphic",
        "cfg": 3.5
    },
    "watercolor": {
        "name": "水彩画調 (Traditional Watercolor)",
        "prefix": "Traditional watercolor painting on cold-press textured paper, visible bleeding paint edges, soft pastel color washes, hand-drawn organic brush strokes, artisanal fine art, translucent delicate watercolor pigments, splashing water droplets",
        "negative": "photorealistic, 3d render, digital vector, sharp harsh digital lines, computer graphics, glossy plastic",
        "cfg": 4.5
    },
    "cinematic": {
        "name": "シネマティック映画調 (Cinematic Film Still)",
        "prefix": "Cinematic movie still, 35mm anamorphic lens, dramatic chiaroscuro volumetric lighting, subtle 35mm film grain, muted cinematic color grading, atmospheric rim light, Panavision film aesthetic, award-winning cinematography",
        "negative": "cartoon, anime, 3d render, plastic, oversaturated, amateur snapshot",
        "cfg": 4.0
    }
}

def main():
    parser = argparse.ArgumentParser(description="Qwen-Image-2.1 Multi-Approach Comparison CLI")
    parser.add_argument("--prompt", type=str, default="A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece, intricate lighting", help="Text prompt")
    parser.add_argument("--negative-prompt", type=str, default="", help="Negative prompt (if empty, uses style default)")
    parser.add_argument("--style", type=str, choices=["none", "anime", "realistic", "watercolor", "cinematic"], default="none", help="Visual art style preset: 'anime', 'realistic', 'watercolor', 'cinematic'")
    parser.add_argument("--approach", type=str, choices=["a", "b", "c"], default="b", help="Generation approach: 'b' (Recommended: 2K Native + 4-bit NF4 Quantization), 'a' (2K Native + Tiled VAE), 'c' (Fast: 1K Native + 2K Upscale)")
    parser.add_argument("--width", type=int, default=2048, help="Target image width (default: 2048)")
    parser.add_argument("--height", type=int, default=2048, help="Target image height")
    parser.add_argument("--steps", type=int, default=20, help="Inference steps")
    parser.add_argument("--guidance-scale", type=float, default=None, help="Classifier-Free Guidance Scale (true_cfg_scale). If not set, uses style preset default")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="outputs/qwen_comparison.png", help="Output file path")
    parser.add_argument("--model-id", type=str, default="Qwen/Qwen-Image-2.1", help="Hugging Face model ID")
    parser.add_argument("--benchmark", action="store_true", help="Print detailed telemetry")

    args = parser.parse_args()

    # スタイルプリセットの適用
    active_prompt = args.prompt
    active_negative = args.negative_prompt
    active_cfg = args.guidance_scale if args.guidance_scale is not None else 4.0

    if args.style != "none" and args.style in STYLE_PRESETS:
        preset = STYLE_PRESETS[args.style]
        active_prompt = f"{preset['prefix']}, {args.prompt}"
        if not active_negative:
            active_negative = preset["negative"]
        if args.guidance_scale is None:
            active_cfg = preset["cfg"]

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    print("=" * 65)
    print(f" Qwen-Image 2.1 Multi-Approach Evaluation: Approach [{args.approach.upper()}]")
    print("=" * 65)
    print(f"Art Style Preset : {args.style.upper()} ({STYLE_PRESETS[args.style]['name'] if args.style in STYLE_PRESETS else 'None'})")
    print(f"Target Resolution: {args.width}x{args.height}")
    print(f"Inference Steps  : {args.steps}")
    print(f"Guidance Scale   : {active_cfg}")
    print(f"Seed             : {args.seed}")
    print(f"Output File      : {args.output}")

    if args.approach == "a":
        print("Approach Strategy: [A] 2K Native Generation with VAE Tiling (Tiled VAE)")
        actual_width, actual_height = args.width, args.height
    elif args.approach == "b":
        print("Approach Strategy: [B] 2K Native Generation with bitsandbytes 4-bit/8-bit Quantization")
        actual_width, actual_height = args.width, args.height
    elif args.approach == "c":
        print("Approach Strategy: [C] 1K Native Generation (1024x1024) + High-Precision Lanczos 2K Upscale")
        actual_width, actual_height = 1024, 1024
    print("-" * 65)

    if not torch.cuda.is_available():
        print("ERROR: CUDA GPU is required.", file=sys.stderr)
        sys.exit(1)

    device_name = torch.cuda.get_device_name(0)
    total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    sys_ram_used, sys_ram_total = get_system_ram_gb()
    print(f"GPU Device       : {device_name} ({total_vram_gb:.2f} GB VRAM)")
    print(f"Host RAM         : {sys_ram_used:.2f} GB / {sys_ram_total:.2f} GB used")
    print("-" * 65)

    from diffusers import DiffusionPipeline

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    print("[1/3] Loading Pipeline...")
    load_start_time = time.time()

    quant_config = None
    if args.approach == "b":
        try:
            from diffusers.quantizers import PipelineQuantizationConfig
            from diffusers import BitsAndBytesConfig as DiffusersBitsAndBytesConfig
            quant_config = PipelineQuantizationConfig(
                quant_mapping={
                    "transformer": DiffusersBitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.bfloat16
                    )
                }
            )
            print(" -> Quantization config prepared (4-bit NF4 for Transformer).")
        except Exception as q_err:
            print(f" -> Quantization setup notice: {q_err}. Falling back to standard offload.")
            quant_config = None

    if quant_config is not None:
        pipe = DiffusionPipeline.from_pretrained(
            args.model_id,
            quantization_config=quant_config,
            torch_dtype=torch.bfloat16
        )
    else:
        pipe = DiffusionPipeline.from_pretrained(
            args.model_id,
            torch_dtype=torch.bfloat16
        )

    # Enable CPU offload to stay within 24GB VRAM
    pipe.enable_model_cpu_offload()

    # Approach A: Enable Tiled VAE on the VAE component
    if args.approach == "a" or max(actual_width, actual_height) >= 2048:
        if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_tiling"):
            pipe.vae.enable_tiling()
            print(" -> [Approach A] pipe.vae.enable_tiling() successfully activated!")
        if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"):
            pipe.vae.enable_slicing()
            print(" -> [Approach A] pipe.vae.enable_slicing() activated.")

    load_elapsed = time.time() - load_start_time
    print(f" -> Pipeline loaded in {load_elapsed:.2f}s")

    generator = None
    if args.seed >= 0:
        generator = torch.Generator(device="cuda").manual_seed(args.seed)

    torch.cuda.reset_peak_memory_stats()

    # 2. Inference
    print(f"[2/3] Generating image ({actual_width}x{actual_height}, {args.steps} steps)...")
    infer_start_time = time.time()

    with torch.inference_mode():
        result = pipe(
            prompt=active_prompt,
            negative_prompt=active_negative,
            width=actual_width,
            height=actual_height,
            num_inference_steps=args.steps,
            true_cfg_scale=active_cfg,
            generator=generator,
            output_resolution=max(actual_width, actual_height),
            use_kv_cache=True
        )
        image = result.images[0]

    infer_elapsed = time.time() - infer_start_time
    infer_vram_peak = torch.cuda.max_memory_allocated() / (1024 ** 3)
    final_ram_used, _ = get_system_ram_gb()

    # 3. Post-processing / Upscale for Approach C
    upscale_elapsed = 0.0
    if args.approach == "c" and (actual_width != args.width or actual_height != args.height):
        print(f" -> [Approach C] Performing Lanczos 2K Upscale: {actual_width}x{actual_height} -> {args.width}x{args.height}...")
        u_start = time.time()
        image = image.resize((args.width, args.height), Image.Resampling.LANCZOS)
        upscale_elapsed = time.time() - u_start
        print(f" -> Upscale completed in {upscale_elapsed:.3f}s")

    # 4. Save Image
    print(f"[3/3] Saving final image to {args.output}...")
    image.save(args.output)
    file_size_mb = os.path.getsize(args.output) / (1024 ** 2)

    total_time = infer_elapsed + upscale_elapsed

    print("\n" + "=" * 65)
    print(f" TELEMETRY REPORT: APPROACH [{args.approach.upper()}]")
    print("=" * 65)
    print(f"Final Resolution     : {image.size[0]} x {image.size[1]}")
    print(f"Native Gen Resolution: {actual_width} x {actual_height}")
    print(f"Inference Steps      : {args.steps} steps")
    print(f"Sampling Time        : {infer_elapsed:.2f} s")
    if args.approach == "c":
        print(f"Upscaling Time       : {upscale_elapsed:.3f} s")
    print(f"Total Time           : {total_time:.2f} s")
    print(f"Sampling Speed       : {infer_elapsed / args.steps:.2f} s/step")
    print(f"Peak GPU VRAM Usage  : {infer_vram_peak:.2f} GB / {total_vram_gb:.2f} GB ({infer_vram_peak / total_vram_gb * 100:.1f}%)")
    print(f"Peak Host RAM Usage  : {final_ram_used:.2f} GB / {sys_ram_total:.2f} GB ({final_ram_used / sys_ram_total * 100:.1f}%)")
    print(f"Output File Size     : {file_size_mb:.2f} MB")
    print("=" * 65)

if __name__ == "__main__":
    main()
