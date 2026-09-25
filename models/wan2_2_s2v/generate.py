#!/usr/bin/env python3
"""Wan2.2-S2V Audio-Driven Video Generation CLI via ComfyUI REST API.

Synchronizes a reference image with an audio track to generate realistic,
lip-synced and rhythm-matched motion videos using Wan 2.2 S2V (14B FP8 scaled).
Supports 4-step Lightning LoRA (super-fast) and multi-chunk video extension.
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Wan2.2-S2V Audio-Driven Video Generation CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to the reference image (PNG/JPG).",
    )
    parser.add_argument(
        "--audio",
        type=str,
        required=True,
        help="Path to the driving audio track (MP3/WAV).",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="A person talking and singing naturally, synchronized with the audio, high quality, realistic expression.",
        help="Text prompt describing the subject and motion.",
    )
    parser.add_argument(
        "--negative_prompt",
        type=str,
        default="色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
        help="Negative prompt for Wan2.2 quality preservation.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/s2v_output.mp4",
        help="Output target file path for the generated video.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Video frame width (e.g. 640, 832, 960). Must be divisible by 16.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=640,
        help="Video frame height (e.g. 640, 480, 544). Must be divisible by 16.",
    )
    parser.add_argument(
        "--num_chunks",
        type=int,
        default=1,
        help="Number of 77-frame chunks to generate. 1 chunk ~4.8s (77 frames @ 16fps), 2 chunks ~9.6s, 3 chunks ~14.4s, 4 chunks ~19.2s.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=16,
        help="Video frames per second (Wan2.2 native is 16fps).",
    )
    parser.add_argument(
        "--lora",
        type=str,
        default="lightning4",
        choices=["lightning4", "none"],
        help="LoRA acceleration: 'lightning4' (4-step fast generation) or 'none' (standard 20-step).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="Sampling steps (default: 4 for lightning4, 20 for none).",
    )
    parser.add_argument(
        "--cfg",
        type=float,
        default=None,
        help="Classifier-Free Guidance scale (default: 1.0 for lightning4, 6.0 for none).",
    )
    parser.add_argument(
        "--skip_first_frames",
        type=int,
        default=4,
        help="Number of initial frames to discard from VAE decode to compensate for first-frame fix duplication and eliminate audio/video lag (default: 4).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for generation.",
    )
    parser.add_argument(
        "--server",
        type=str,
        default="http://127.0.0.1:8188",
        help="ComfyUI server base URL.",
    )
    return parser.parse_args()


def upload_file_to_comfy(server_url: str, file_path: str) -> str:
    """Upload an image or audio file to ComfyUI input folder via REST API."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    url = f"{server_url.rstrip('/')}/upload/image"
    boundary = uuid.uuid4().hex
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    with open(path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))
        uploaded_name = resp_data.get("name", path.name)
        print(f"[Upload] Uploaded {path.name} -> {uploaded_name}")
        return uploaded_name


def build_s2v_prompt_graph(
    image_filename: str,
    audio_filename: str,
    prompt_text: str,
    negative_prompt_text: str,
    width: int = 640,
    height: int = 640,
    num_chunks: int = 1,
    fps: int = 16,
    skip_first_frames: int = 4,
    use_lightning: bool = True,
    steps: int = 4,
    cfg: float = 1.0,
    seed: int = 42,
) -> dict:
    """Construct a full ComfyUI API prompt dictionary for Wan2.2-S2V with optional multi-chunk extension."""
    prompt = {}

    # Node 1: UNETLoader (Wan2.2 S2V 14B FP8)
    prompt["1"] = {
        "class_type": "UNETLoader",
        "inputs": {
            "unet_name": "wan2.2_s2v_14B_fp8_scaled.safetensors",
            "weight_dtype": "default",
        },
    }

    # Model connection routing (with or without Lightning LoRA)
    current_model_node = "1"
    if use_lightning:
        # Node 2: LoraLoaderModelOnly
        prompt["2"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": [current_model_node, 0],
                "lora_name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
                "strength_model": 1.0,
            },
        }
        current_model_node = "2"

    # Node 3: ModelSamplingSD3 (shift=8.0 for Wan2.2)
    prompt["3"] = {
        "class_type": "ModelSamplingSD3",
        "inputs": {
            "model": [current_model_node, 0],
            "shift": 8.0,
        },
    }
    model_output = ["3", 0]

    # Node 4: CLIPLoader (UMT5 XXL FP8)
    prompt["4"] = {
        "class_type": "CLIPLoader",
        "inputs": {
            "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
            "type": "wan",
            "device": "default",
        },
    }

    # Node 5: CLIPTextEncode (Positive Prompt)
    prompt["5"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 0],
            "text": prompt_text,
        },
    }

    # Node 6: CLIPTextEncode (Negative Prompt)
    prompt["6"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 0],
            "text": negative_prompt_text,
        },
    }

    # Node 7: VAELoader (Wan 2.1 VAE)
    prompt["7"] = {
        "class_type": "VAELoader",
        "inputs": {
            "vae_name": "wan_2.1_vae.safetensors",
        },
    }

    # Node 8: LoadImage
    prompt["8"] = {
        "class_type": "LoadImage",
        "inputs": {
            "image": image_filename,
        },
    }

    # Node 9: LoadAudio
    prompt["9"] = {
        "class_type": "LoadAudio",
        "inputs": {
            "audio": audio_filename,
        },
    }

    # Node 10: AudioEncoderLoader (Wav2Vec2)
    prompt["10"] = {
        "class_type": "AudioEncoderLoader",
        "inputs": {
            "audio_encoder_name": "wav2vec2_large_english_fp16.safetensors",
        },
    }

    # Node 11: AudioEncoderEncode
    prompt["11"] = {
        "class_type": "AudioEncoderEncode",
        "inputs": {
            "audio_encoder": ["10", 0],
            "audio": ["9", 0],
        },
    }

    # Node 12: WanSoundImageToVideo (Initial Chunk)
    prompt["12"] = {
        "class_type": "WanSoundImageToVideo",
        "inputs": {
            "positive": ["5", 0],
            "negative": ["6", 0],
            "vae": ["7", 0],
            "audio_encoder_output": ["11", 0],
            "ref_image": ["8", 0],
            "width": width,
            "height": height,
            "length": 77,
            "batch_size": 1,
        },
    }

    # Node 13: KSampler (Initial Chunk Denoise)
    prompt["13"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": model_output,
            "positive": ["12", 0],
            "negative": ["12", 1],
            "latent_image": ["12", 2],
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": "uni_pc",
            "scheduler": "simple",
            "denoise": 1.0,
        },
    }

    current_latent = ["13", 0]
    next_node_id = 20

    # Multi-chunk Extension (if num_chunks > 1)
    for chunk_idx in range(1, num_chunks):
        extend_node = str(next_node_id)
        sampler_node = str(next_node_id + 1)
        concat_node = str(next_node_id + 2)
        next_node_id += 3

        prompt[extend_node] = {
            "class_type": "WanSoundImageToVideoExtend",
            "inputs": {
                "positive": ["5", 0],
                "negative": ["6", 0],
                "vae": ["7", 0],
                "video_latent": current_latent,
                "audio_encoder_output": ["11", 0],
                "ref_image": ["8", 0],
                "length": 77,
            },
        }

        prompt[sampler_node] = {
            "class_type": "KSampler",
            "inputs": {
                "model": model_output,
                "positive": [extend_node, 0],
                "negative": [extend_node, 1],
                "latent_image": [extend_node, 2],
                "seed": seed + chunk_idx,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "uni_pc",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        }

        prompt[concat_node] = {
            "class_type": "LatentConcat",
            "inputs": {
                "samples1": current_latent,
                "samples2": [sampler_node, 0],
                "dim": "t",
            },
        }
        current_latent = [concat_node, 0]

    # First-frame fix: Duplicate frame 0, decode, then skip frame 0 to avoid VAE overbaked artifact
    cut_node = str(next_node_id)
    concat_fix_node = str(next_node_id + 1)
    decode_node = str(next_node_id + 2)
    crop_batch_node = str(next_node_id + 3)
    create_video_node = str(next_node_id + 4)
    save_video_node = str(next_node_id + 5)

    prompt[cut_node] = {
        "class_type": "LatentCut",
        "inputs": {
            "samples": current_latent,
            "dim": "t",
            "index": 0,
            "amount": 1,
        },
    }

    prompt[concat_fix_node] = {
        "class_type": "LatentConcat",
        "inputs": {
            "samples1": [cut_node, 0],
            "samples2": current_latent,
            "dim": "t",
        },
    }

    prompt[decode_node] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": [concat_fix_node, 0],
            "vae": ["7", 0],
        },
    }

    prompt[crop_batch_node] = {
        "class_type": "ImageFromBatch",
        "inputs": {
            "image": [decode_node, 0],
            "batch_index": skip_first_frames,
            "length": 4096,
        },
    }

    prompt[create_video_node] = {
        "class_type": "CreateVideo",
        "inputs": {
            "images": [crop_batch_node, 0],
            "audio": ["9", 0],
            "fps": float(fps),
        },
    }

    prompt[save_video_node] = {
        "class_type": "SaveVideo",
        "inputs": {
            "video": [create_video_node, 0],
            "filename_prefix": "video/Wan2_2_S2V",
            "format": "auto",
        },
    }

    return prompt, save_video_node


def wait_for_execution(server_url: str, prompt_id: str, timeout: int = 1800) -> dict:
    """Poll ComfyUI /history endpoint until execution finishes or fails."""
    start_time = time.time()
    last_print = 0

    while time.time() - start_time < timeout:
        time.sleep(3)
        elapsed = time.time() - start_time
        if elapsed - last_print > 15:
            print(f"[Progress] Generation in progress... ({elapsed:.1f}s elapsed)")
            last_print = elapsed

        try:
            req = urllib.request.Request(f"{server_url.rstrip('/')}/history/{prompt_id}")
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if prompt_id in data:
                    item = data[prompt_id]
                    status = item.get("status", {})
                    if status.get("completed", False):
                        print(f"[Done] Execution completed successfully in {elapsed:.1f}s!")
                        return item
                    if status.get("status_str") == "error":
                        messages = status.get("messages", [])
                        raise RuntimeError(f"ComfyUI execution error: {messages}")
        except urllib.error.URLError:
            pass

    raise TimeoutError(f"Generation timed out after {timeout} seconds")


def download_output_video(server_url: str, history_item: dict, target_output: str, save_node_id: str):
    """Retrieve output video file from ComfyUI and save locally."""
    outputs = history_item.get("outputs", {})
    save_output = outputs.get(save_node_id, {})
    videos = save_output.get("videos", []) or save_output.get("images", [])

    if not videos:
        # Fallback search across all output nodes
        for nid, val in outputs.items():
            if "videos" in val and val["videos"]:
                videos = val["videos"]
                break

    if not videos:
        raise RuntimeError(f"No video found in execution outputs: {json.dumps(outputs, indent=2)}")

    video_info = videos[0]
    filename = video_info.get("filename")
    subfolder = video_info.get("subfolder", "")
    folder_type = video_info.get("type", "output")

    query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    url = f"{server_url.rstrip('/')}/view?{query}"

    print(f"[Download] Fetching video from {url} ...")
    Path(target_output).parent.mkdir(parents=True, exist_ok=True)

    urllib.request.urlretrieve(url, target_output)
    size_mb = os.path.getsize(target_output) / (1024 * 1024)
    print(f"[SUCCESS] Video saved: {target_output} ({size_mb:.2f} MB)")


def main():
    args = parse_args()
    server = args.server.rstrip("/")

    # Determine steps and CFG defaults based on LoRA mode
    use_lightning = args.lora == "lightning4"
    steps = args.steps if args.steps is not None else (4 if use_lightning else 20)
    cfg = args.cfg if args.cfg is not None else (1.0 if use_lightning else 6.0)

    print("==================================================")
    print("Wan2.2-S2V Audio-Driven Video Generation")
    print("==================================================")
    print(f"Reference Image : {args.image}")
    print(f"Audio Track     : {args.audio}")
    print(f"Prompt          : {args.prompt}")
    print(f"Resolution      : {args.width}x{args.height}")
    print(f"FPS             : {args.fps}")
    print(f"Chunks          : {args.num_chunks} chunk(s) ({(args.num_chunks * 77) / args.fps:.1f}s total)")
    print(f"Mode            : {'4-step Lightning' if use_lightning else '20-step Standard'}")
    print(f"Steps / CFG     : {steps} steps / CFG {cfg}")
    print(f"Seed            : {args.seed}")
    print(f"Output File     : {args.output}")
    print(f"ComfyUI Server  : {server}")
    print("==================================================")

    # 1. Upload Image and Audio to ComfyUI
    print("\n--- [1/4] Uploading Media to ComfyUI ---")
    uploaded_image = upload_file_to_comfy(server, args.image)
    uploaded_audio = upload_file_to_comfy(server, args.audio)

    # 2. Build Prompt Graph
    print("\n--- [2/4] Constructing Workflow Graph ---")
    prompt_graph, save_node_id = build_s2v_prompt_graph(
        image_filename=uploaded_image,
        audio_filename=uploaded_audio,
        prompt_text=args.prompt,
        negative_prompt_text=args.negative_prompt,
        width=args.width,
        height=args.height,
        num_chunks=args.num_chunks,
        fps=args.fps,
        skip_first_frames=args.skip_first_frames,
        use_lightning=use_lightning,
        steps=steps,
        cfg=cfg,
        seed=args.seed,
    )

    # 3. Queue Execution via REST API
    print("\n--- [3/4] Queuing Generation via REST API ---")
    req_body = json.dumps({"prompt": prompt_graph}).encode("utf-8")
    req = urllib.request.Request(
        f"{server}/prompt",
        data=req_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            prompt_id = resp_data.get("prompt_id")
            if not prompt_id:
                raise RuntimeError(f"Failed to queue prompt: {resp_data}")
            print(f"[Queue] Task queued with Prompt ID: {prompt_id}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] ComfyUI rejected prompt ({e.code} {e.reason}):\n{error_body}", file=sys.stderr)
        raise

    # 4. Wait for Execution and Download Video
    print("\n--- [4/4] Monitoring Execution Progress ---")
    history_item = wait_for_execution(server, prompt_id)
    download_output_video(server, history_item, args.output, save_node_id)
    print("\n=== Generation Process Completed Successfully ===")


if __name__ == "__main__":
    main()
