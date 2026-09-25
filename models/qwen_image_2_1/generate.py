#!/usr/bin/env python3
"""
Qwen-Image-2.1 Text-to-Image Generation & Benchmarking CLI
Supports 1K, 2K (2048x2048), RGBA transparency, and detailed resource telemetry.
"""

import argparse
import os
import sys
import time
import psutil
import torch

def get_ram_usage_gb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def get_system_ram_gb():
    mem = psutil.virtual_memory()
    return mem.used / (1024 ** 3), mem.total / (1024 ** 3)

def main():
    parser = argparse.ArgumentParser(description="Qwen-Image-2.1 Generation & Benchmark CLI")
    parser.add_argument("--prompt", type=str, default="A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece, intricate lighting", help="Text prompt")
    parser.add_argument("--negative-prompt", type=str, default="worst quality, low quality, blurry, distorted, deformed, bad anatomy, text, watermark", help="Negative prompt")
    parser.add_argument("--width", type=int, default=1024, help="Image width (e.g. 1024, 2048)")
    parser.add_argument("--height", type=int, default=1024, help="Image height (e.g. 1024, 2048)")
    parser.add_argument("--steps", type=int, default=25, help="Number of inference steps")
    parser.add_argument("--guidance-scale", type=float, default=4.0, help="Classifier-Free Guidance Scale")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (-1 for random)")
    parser.add_argument("--output", type=str, default="outputs/qwen_image_output.png", help="Output file path")
    parser.add_argument("--model-id", type=str, default="Qwen/Qwen-Image-2.1", help="Hugging Face model ID")
    parser.add_argument("--benchmark", action="store_true", help="Print detailed benchmark and telemetry report")

    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    print("=" * 60)
    print(" Qwen-Image 2.1 Generation & Benchmark")
    print("=" * 60)
    print(f"Model ID       : {args.model_id}")
    print(f"Resolution     : {args.width}x{args.height}")
    print(f"Inference Steps: {args.steps}")
    print(f"Guidance Scale : {args.guidance_scale}")
    print(f"Seed           : {args.seed}")
    print(f"Output         : {args.output}")
    print("-" * 60)

    # Check CUDA device
    if not torch.cuda.is_available():
        print("ERROR: CUDA device not found. An NVIDIA GPU (e.g., L4 24GB) is required.", file=sys.stderr)
        sys.exit(1)

    device_name = torch.cuda.get_device_name(0)
    total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    sys_ram_used, sys_ram_total = get_system_ram_gb()

    print(f"GPU Device     : {device_name} ({total_vram_gb:.2f} GB VRAM)")
    print(f"System RAM     : {sys_ram_used:.2f} GB / {sys_ram_total:.2f} GB used")
    print("-" * 60)

    # Import diffusers
    from diffusers import DiffusionPipeline

    # Reset CUDA memory stats
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    # 1. Pipeline Load
    print("[1/3] Loading Qwen-Image-2.1 Pipeline...")
    load_start_time = time.time()
    pipe = DiffusionPipeline.from_pretrained(
        args.model_id,
        torch_dtype=torch.bfloat16
    )
    pipe.enable_model_cpu_offload()
    if hasattr(pipe, "enable_vae_tiling"):
        pipe.enable_vae_tiling()
    if hasattr(pipe, "enable_vae_slicing"):
        pipe.enable_vae_slicing()

    load_elapsed = time.time() - load_start_time
    load_vram_peak = torch.cuda.max_memory_allocated() / (1024 ** 3)
    load_ram_used, _ = get_system_ram_gb()

    print(f" -> Pipeline loaded in {load_elapsed:.2f}s")
    print(f" -> Post-load VRAM peak: {load_vram_peak:.2f} GB")
    print(f" -> Post-load System RAM: {load_ram_used:.2f} GB")

    # 2. Setup Generator
    generator = None
    if args.seed >= 0:
        generator = torch.Generator(device="cuda").manual_seed(args.seed)

    # Reset peak memory stats before inference
    torch.cuda.reset_peak_memory_stats()

    # 3. Inference
    print(f"[2/3] Generating image ({args.width}x{args.height}, {args.steps} steps)...")
    infer_start_time = time.time()

    with torch.inference_mode():
        if max(args.width, args.height) >= 2048:
            print(" -> 2K resolution detected: using staged memory decode (unloading transformer before VAE)...")
            latents_out = pipe(
                prompt=args.prompt,
                negative_prompt=args.negative_prompt,
                width=args.width,
                height=args.height,
                num_inference_steps=args.steps,
                true_cfg_scale=args.guidance_scale,
                generator=generator,
                output_resolution=max(args.width, args.height),
                use_kv_cache=True,
                output_type="latent"
            )
            latents = latents_out.images

            # Explicitly offload transformer and clear CUDA cache to free ~14GB VRAM
            pipe.transformer.to("cpu")
            torch.cuda.empty_cache()

            # VAE decode with full VRAM availability
            pipe.vae.to("cuda")
            unpacked_latents = pipe._unpack_latents(latents, args.height, args.width, pipe.vae_scale_factor)
            unpacked_latents = unpacked_latents.to(pipe.vae.dtype)
            latents_mean = (
                torch.tensor(pipe.vae.config.latents_mean)
                .view(1, pipe.vae.config.z_dim, 1, 1, 1)
                .to(unpacked_latents.device, unpacked_latents.dtype)
            )
            latents_std = (
                torch.tensor(pipe.vae.config.latents_std)
                .view(1, pipe.vae.config.z_dim, 1, 1, 1)
                .to(unpacked_latents.device, unpacked_latents.dtype)
            )
            norm_latents = unpacked_latents * latents_std + latents_mean
            decoded = pipe.vae.decode(norm_latents, return_dict=False)[0][:, :, 0]
            image = pipe.image_processor.postprocess(decoded, output_type="pil")[0]
        else:
            result = pipe(
                prompt=args.prompt,
                negative_prompt=args.negative_prompt,
                width=args.width,
                height=args.height,
                num_inference_steps=args.steps,
                true_cfg_scale=args.guidance_scale,
                generator=generator,
                output_resolution=max(args.width, args.height),
                use_kv_cache=True
            )
            image = result.images[0]

    # 4. Save image
    print(f"[3/3] Saving result to {args.output}...")
    image.save(args.output)
    file_size_mb = os.path.getsize(args.output) / (1024 ** 2)
    print(f" -> Image saved ({file_size_mb:.2f} MB, {image.size[0]}x{image.size[1]})")

    # Benchmark Telemetry Summary
    print("\n" + "=" * 60)
    print(" TELEMETRY & BENCHMARK REPORT")
    print("=" * 60)
    print(f"Resolution          : {args.width} x {args.height} ({'2K' if max(args.width, args.height) >= 2048 else '1K/Standard'})")
    print(f"Inference Steps     : {args.steps} steps")
    print(f"Model Load Time     : {load_elapsed:.2f} s")
    print(f"Total Inference Time: {infer_elapsed:.2f} s")
    print(f"Sampling Speed      : {sec_per_step:.2f} s/step ({args.steps / infer_elapsed:.2f} steps/s)")
    print(f"Peak GPU VRAM Usage : {infer_vram_peak:.2f} GB / {total_vram_gb:.2f} GB ({infer_vram_peak / total_vram_gb * 100:.1f}%)")
    print(f"Peak Host RAM Usage : {final_ram_used:.2f} GB / {sys_ram_total:.2f} GB ({final_ram_used / sys_ram_total * 100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    main()
