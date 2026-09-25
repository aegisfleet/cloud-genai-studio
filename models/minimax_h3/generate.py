#!/usr/bin/env python3
"""MiniMax H3 CLI: Reference-to-Video+Audio (Ref2VA), Image-to-Video, Text-to-Video

ComfyUI REST API を経由して MiniMax H3 (DiT int8 convrot + Qwen3VL nvfp4 + Turbo LoRA)
による高品質な動画（音声同期）を生成する。複数画像リファレンス対応。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request


def wait_for_server(server_url: str, timeout: int = 120) -> bool:
    """ComfyUI サーバーの起動と応答を待機する。"""
    print(f"[Wait] Checking ComfyUI server at {server_url} ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{server_url}/system_stats", timeout=5) as resp:
                if resp.status == 200:
                    print(f"[Ready] ComfyUI server is online! ({time.time() - start:.1f}s waited)")
                    return True
        except Exception:
            time.sleep(3)
    print(f"[Timeout] ComfyUI server failed to respond within {timeout}s.")
    return False


def upload_file(server_url: str, file_path: str, subfolder: str = "") -> str:
    """ComfyUI の /upload/image エンドポイントにファイル（画像または音声）をアップロードする。"""
    filename = os.path.basename(file_path)
    url = f"{server_url}/upload/image"
    boundary = "----WebKitFormBoundary" + hex(int(time.time() * 1000))[2:]

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + file_bytes + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="overwrite"\r\n\r\n'
        f"true\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("name", filename)
    except urllib.error.HTTPError as e:
        print(f"[Upload Error] HTTP {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)


def format_prompt(prompt_text: str) -> str:
    """SNS/Director用の @[character ref] 記法などを ComfyUI MiniMaxH3 の <Picture 1> 記法に変換する。"""
    cleaned = prompt_text
    cleaned = re.sub(r"@\[(?:character(?:\s*ref)?|image|pic)\]", "<Picture 1>", cleaned, flags=re.IGNORECASE)
    if "<Picture" not in cleaned:
        cleaned = f"<Picture 1> {cleaned}"
    return cleaned.strip()


def build_ref2va_workflow(
    image_names: list[str],
    audio_name: str = "",
    prompt_text: str = "",
    width: int = 640,
    height: int = 640,
    length: int = 360,
    steps: int = 8,
    sampler_name: str = "euler",
    seed: int = 42,
    output_prefix: str = "video/MiniMax_H3_Ref2VA",
) -> dict:
    """MiniMax H3 ReferenceToVideo ワークフローを構築する（複数画像リファレンス対応）。"""
    formatted_prompt = format_prompt(prompt_text)

    workflow = {
        "3": {
            "inputs": {
                "unet_name": "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
                "weight_dtype": "default",
            },
            "class_type": "UNETLoader",
        },
        "4": {
            "inputs": {
                "clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
                "type": "minimax",
            },
            "class_type": "CLIPLoader",
        },
        "5": {
            "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"},
            "class_type": "VAELoader",
        },
        "6": {
            "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"},
            "class_type": "VAELoader",
        },
        "7": {
            "inputs": {
                "lora_name": "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
                "strength_model": 1.0,
                "model": ["3", 0],
            },
            "class_type": "LoraLoaderModelOnly",
        },
        "8": {
            "inputs": {
                "clip": ["4", 0],
                "vae": ["5", 0],
                "audio_vae": ["6", 0],
                "prompt": formatted_prompt,
                "width": int(width),
                "height": int(height),
                "length": int(length),
                "ref_image_size": "match",
            },
            "class_type": "MiniMaxH3ReferenceToVideo",
        },
        "9": {
            "inputs": {
                "model": ["7", 0],
                "conditioning": ["8", 0],
            },
            "class_type": "BasicGuider",
        },
        "10": {
            "inputs": {"sampler_name": sampler_name},
            "class_type": "KSamplerSelect",
        },
        "11": {
            "inputs": {
                "model": ["7", 0],
                "scheduler": "simple",
                "steps": int(steps),
                "denoise": 1.0,
            },
            "class_type": "BasicScheduler",
        },
        "12": {
            "inputs": {"noise_seed": int(seed)},
            "class_type": "RandomNoise",
        },
        "13": {
            "inputs": {
                "noise": ["12", 0],
                "guider": ["9", 0],
                "sampler": ["10", 0],
                "sigmas": ["11", 0],
                "latent_image": ["8", 1],
            },
            "class_type": "SamplerCustomAdvanced",
        },
        "14": {
            "inputs": {
                "samples": ["13", 0],
                "vae": ["5", 0],
            },
            "class_type": "VAEDecode",
        },
        "15": {
            "inputs": {
                "samples": ["13", 0],
                "vae": ["6", 0],
            },
            "class_type": "VAEDecodeAudio",
        },
        "16": {
            "inputs": {
                "images": ["14", 0],
                "audio": ["15", 0],
                "fps": 24.0,
            },
            "class_type": "CreateVideo",
        },
        "17": {
            "inputs": {
                "video": ["16", 0],
                "filename_prefix": output_prefix,
                "format": "auto",
            },
            "class_type": "SaveVideo",
        },
    }

    # 各画像スロット（<Picture 1>, <Picture 2>, ...）を動的に生成
    for idx, img_name in enumerate(image_names):
        node_id = str(20 + idx)
        workflow[node_id] = {
            "inputs": {"image": img_name},
            "class_type": "LoadImage",
        }
        workflow["8"]["inputs"][f"ref_images.ref_image_{idx}"] = [node_id, 0]

    # 音声入力が提供されている場合は LoadAudio を追加してバインド
    if audio_name:
        workflow["2"] = {
            "inputs": {"audio": audio_name},
            "class_type": "LoadAudio",
        }
        workflow["8"]["inputs"]["ref_audios.ref_audio_0"] = ["2", 0]

    return workflow


def wait_for_completion(server_url: str, prompt_id: str, timeout: int = 3600) -> dict:
    """ComfyUI の実行完了を待機し、出力ファイル情報を取得する。"""
    start_time = time.time()
    last_print = 0

    while time.time() - start_time < timeout:
        time.sleep(5)
        elapsed = time.time() - start_time
        if elapsed - last_print > 20:
            print(f"[Progress] Generation running... ({elapsed:.1f}s elapsed)")
            last_print = elapsed

        try:
            url = f"{server_url}/history/{prompt_id}"
            with urllib.request.urlopen(url) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if prompt_id in data:
                    entry = data[prompt_id]
                    status = entry.get("status", {})
                    if status.get("status_str") == "success":
                        print(f"[Success] Completed in {elapsed:.1f} seconds!")
                        return entry.get("outputs", {})
                    elif status.get("status_str") == "error":
                        print(f"[Error] Execution failed: {json.dumps(status, indent=2)}")
                        sys.exit(1)
        except Exception:
            pass

    print("[Timeout] Generation exceeded time limit.")
    sys.exit(1)


def download_video(server_url: str, outputs: dict, output_dir: str) -> str:
    """SaveVideo ノードから出力された動画ファイルをローカルに保存する。"""
    os.makedirs(output_dir, exist_ok=True)
    video_info = None

    for node_id, output in outputs.items():
        if "images" in output:
            for item in output["images"]:
                if item.get("filename", "").endswith((".mp4", ".mov", ".mkv", ".webm")):
                    video_info = item
                    break
        if "video" in output:
            for item in output["video"]:
                if item.get("filename", "").endswith((".mp4", ".mov", ".mkv", ".webm")):
                    video_info = item
                    break

    if not video_info:
        print("[Warning] No video file found in output.")
        return ""

    filename = video_info["filename"]
    subfolder = video_info.get("subfolder", "")
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    download_url = f"{server_url}/view?{params}"
    dest_path = os.path.join(output_dir, filename)

    print(f"[Download] Saving video to {dest_path} ...")
    urllib.request.urlretrieve(download_url, dest_path)
    return dest_path


def main():
    parser = argparse.ArgumentParser(description="MiniMax H3 CLI")
    parser.add_argument("--image", type=str, default="", help="Input primary character image or comma-separated images")
    parser.add_argument("--images", nargs="+", default=[], help="List of reference images (<Picture 1>, <Picture 2>, ...)")
    parser.add_argument("--audio", type=str, default="", help="Optional input speech or reference audio (MP3/WAV)")
    parser.add_argument(
        "--prompt",
        type=str,
        default="",
        help="Prompt text containing <Picture 1>, <Picture 2>, etc.",
    )
    parser.add_argument("--prompt_file", type=str, default="", help="Path to text file containing prompt")
    parser.add_argument("--width", type=int, default=640, help="Video width (default: 640)")
    parser.add_argument("--height", type=int, default=640, help="Video height (default: 640)")
    parser.add_argument("--length", type=int, default=360, help="Frames count at 24fps (360 = 15s)")
    parser.add_argument("--steps", type=int, default=8, help="Sampling steps (default: 8 for better audio/motion)")
    parser.add_argument("--sampler", type=str, default="euler", help="Sampler name (default: euler, less audio noise)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--server_url", type=str, default="http://127.0.0.1:8188", help="ComfyUI server URL")
    parser.add_argument("--output_dir", type=str, default="./outputs", help="Directory to save generated video")
    args = parser.parse_args()

    # 画像リストの結合・解析
    raw_images = []
    if args.images:
        raw_images.extend(args.images)
    if args.image:
        raw_images.extend([x.strip() for x in args.image.split(",") if x.strip()])

    if not raw_images:
        print("[Error] No input images specified via --image or --images.")
        sys.exit(1)

    prompt_text = args.prompt
    if args.prompt_file and os.path.exists(args.prompt_file):
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt_text = f.read().strip()

    if not prompt_text:
        prompt_text = "<Picture 1> A fast, striking character reveal."

    print("=== MiniMax H3 Reference-to-Video+Audio CLI ===")
    print(f"Reference Images ({len(raw_images)} items):")
    for i, p in enumerate(raw_images):
        print(f"  <Picture {i+1}>: {p}")
    if args.audio:
        print(f"Audio: {args.audio}")
    else:
        print("Audio: (None - Native SFX/Sound Synthesis)")
    print(f"Resolution: {args.width}x{args.height}, Length: {args.length} frames ({args.length/24.0:.1f}s)")
    print(f"Sampling: {args.steps} steps with '{args.sampler}' sampler (Seed: {args.seed})")

    # 1. Wait for ComfyUI and Upload assets
    if not wait_for_server(args.server_url, timeout=120):
        print(f"[Error] Could not reach ComfyUI server at {args.server_url}")
        sys.exit(1)

    uploaded_images = []
    for i, img_path in enumerate(raw_images):
        print(f"[1/3] Uploading reference image {i+1}/{len(raw_images)}: {img_path} ...")
        uploaded_images.append(upload_file(args.server_url, img_path))

    uploaded_audio = ""
    if args.audio and os.path.exists(args.audio):
        print("[1/3] Uploading input audio to ComfyUI...")
        uploaded_audio = upload_file(args.server_url, args.audio)

    # 2. Build and submit workflow
    print("[2/3] Submitting workflow...")
    workflow = build_ref2va_workflow(
        image_names=uploaded_images,
        audio_name=uploaded_audio,
        prompt_text=prompt_text,
        width=args.width,
        height=args.height,
        length=args.length,
        steps=args.steps,
        sampler_name=args.sampler,
        seed=args.seed,
    )

    req_data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{args.server_url}/prompt",
        data=req_data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            prompt_id = res["prompt_id"]
            print(f"Queued successfully! prompt_id: {prompt_id}")
    except urllib.error.HTTPError as e:
        print(f"[Error] Failed to submit prompt: {e.read().decode('utf-8')}")
        sys.exit(1)

    # 3. Wait and download
    print("[3/3] Waiting for generation...")
    outputs = wait_for_completion(args.server_url, prompt_id, timeout=3600)
    saved_file = download_video(args.server_url, outputs, args.output_dir)
    print(f"All done! Saved file: {saved_file}")


if __name__ == "__main__":
    main()
