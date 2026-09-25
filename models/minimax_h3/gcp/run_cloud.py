#!/usr/bin/env python3
"""
MiniMax H3 Cloud Generation Orchestrator (Python)
Eliminates PowerShell parsing/quoting issues by managing GCP operations via native subprocess.
"""

import argparse
import os
import subprocess
import sys
import time

import shutil

INSTANCE_NAME = "minimax-h3-l4-spot"
ZONE = "asia-east1-b"
MACHINE_TYPE = "g2-standard-8"
REMOTE_HOME = "/home/raizi/minimax-h3"

GCLOUD_BIN = shutil.which("gcloud") or shutil.which("gcloud.cmd") or "gcloud"

def run_cmd(cmd_list, check=True, capture_output=False, text=True):
    if cmd_list and cmd_list[0] == "gcloud":
        cmd_list[0] = GCLOUD_BIN
    print(f"[CMD] {' '.join(cmd_list)}")
    res = subprocess.run(cmd_list, check=check, capture_output=capture_output, text=text, encoding='utf-8', errors='replace', shell=(os.name == 'nt'))
    return res

def main():
    parser = argparse.ArgumentParser(description="Run MiniMax H3 Generation on GCP Spot Instance")
    parser.add_argument("--image_file", type=str, default="examples/images/miyabi_reveal_images.txt")
    parser.add_argument("--images", nargs="+", default=None)
    parser.add_argument("--prompt_file", type=str, default="examples/prompts/miyabi_reveal_sfx_multi.txt")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=640)
    parser.add_argument("--length", type=int, default=360)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--sampler", type=str, default="euler")
    parser.add_argument("--keep_running", action="store_true", help="Do not stop instance after generation")
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    # 1. Resolve Reference Images
    image_paths = []
    if args.images:
        for p in args.images:
            full_p = p if os.path.isabs(p) else os.path.join(repo_root, p)
            if os.path.exists(full_p):
                image_paths.append(full_p)
            else:
                print(f"[Warning] Image not found: {full_p}")
    elif args.image_file:
        full_f = args.image_file if os.path.isabs(args.image_file) else os.path.join(repo_root, args.image_file)
        if os.path.exists(full_f):
            with open(full_f, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        p = line if os.path.isabs(line) else os.path.join(repo_root, line)
                        if os.path.exists(p):
                            image_paths.append(p)
                        else:
                            print(f"[Warning] Image from file not found: {p}")

    if not image_paths:
        default_img = os.path.join(repo_root, "examples", "images", "hoshimi_miyabi.png")
        if os.path.exists(default_img):
            image_paths.append(default_img)
        else:
            print("[Error] No valid reference images found.")
            sys.exit(1)

    print("==========================================================")
    print(" MiniMax H3 Multi-Reference Studio (Python Runner)        ")
    print("==========================================================")
    print(f"Instance   : {INSTANCE_NAME} (Zone: {ZONE})")
    print(f"Resolution : {args.width}x{args.height}, Length: {args.length} frames ({args.length/24:.1f}s)")
    print(f"Sampling   : {args.steps} steps ({args.sampler} sampler)")
    print(f"Images ({len(image_paths)} references):")
    for i, img in enumerate(image_paths, start=1):
        print(f"  <Picture {i}>: {img}")
    print("==========================================================")

    # 2. Check / Start GCP Instance
    print("\n=== 1. Checking / Starting Spot Instance ===")
    status_proc = run_cmd([
        "gcloud", "compute", "instances", "list",
        f"--filter=name={INSTANCE_NAME} AND zone:{ZONE}",
        "--format=value(status)"
    ], capture_output=True)
    status = status_proc.stdout.strip()
    print(f"Current instance status: '{status}'")

    if status != "RUNNING":
        print(f"Starting instance {INSTANCE_NAME}...")
        run_cmd(["gcloud", "compute", "instances", "start", INSTANCE_NAME, f"--zone={ZONE}"])

    # 3. Wait for SSH & GPU Ready
    print("\n=== 2. Testing SSH & NVIDIA GPU Status ===")
    for attempt in range(1, 21):
        print(f"Checking SSH attempt {attempt}/20...")
        try:
            res = run_cmd([
                "gcloud", "compute", "ssh", INSTANCE_NAME, f"--zone={ZONE}",
                "--command=nvidia-smi --query-gpu=name,memory.total --format=csv,noheader"
            ], capture_output=True)
            if "L4" in res.stdout:
                print(f"GPU is Ready: {res.stdout.strip()}")
                break
        except subprocess.CalledProcessError:
            pass
        time.sleep(10)

    # 4. Prepare Remote Directory
    run_cmd([
        "gcloud", "compute", "ssh", INSTANCE_NAME, f"--zone={ZONE}",
        f"--command=mkdir -p {REMOTE_HOME}/outputs"
    ])

    # 5. Sync Scripts and Reference Images
    print("\n=== 3. Syncing Scripts and Reference Images ===")
    local_gen = os.path.join(repo_root, "models", "minimax_h3", "generate.py")
    local_sh = os.path.join(repo_root, "models", "minimax_h3", "gcp", "run_remote.sh")
    run_cmd(["gcloud", "compute", "scp", local_gen, f"{INSTANCE_NAME}:{REMOTE_HOME}/generate.py", f"--zone={ZONE}"])
    run_cmd(["gcloud", "compute", "scp", local_sh, f"{INSTANCE_NAME}:{REMOTE_HOME}/run_remote.sh", f"--zone={ZONE}"])

    remote_images = []
    for img_path in image_paths:
        leaf = os.path.basename(img_path)
        print(f"Uploading {leaf}...")
        run_cmd(["gcloud", "compute", "scp", img_path, f"{INSTANCE_NAME}:{REMOTE_HOME}/{leaf}", f"--zone={ZONE}"])
        remote_images.append(f"{REMOTE_HOME}/{leaf}")

    # Sync prompt
    full_prompt_f = args.prompt_file if os.path.isabs(args.prompt_file) else os.path.join(repo_root, args.prompt_file)
    if os.path.exists(full_prompt_f):
        run_cmd(["gcloud", "compute", "scp", full_prompt_f, f"{INSTANCE_NAME}:{REMOTE_HOME}/prompt.txt", f"--zone={ZONE}"])

    # 6. Execute Remote Generation
    print("\n=== 4. Executing MiniMax H3 Generation on VM ===")
    remote_imgs_arg = " ".join(remote_images)
    exec_cmd = (
        f"chmod +x {REMOTE_HOME}/run_remote.sh && "
        f"{REMOTE_HOME}/run_remote.sh "
        f"--images {remote_imgs_arg} "
        f"--prompt_file {REMOTE_HOME}/prompt.txt "
        f"--width {args.width} --height {args.height} "
        f"--length {args.length} --steps {args.steps} --sampler {args.sampler}"
    )

    try:
        run_cmd([
            "gcloud", "compute", "ssh", INSTANCE_NAME, f"--zone={ZONE}",
            f"--command={exec_cmd}"
        ])
    except subprocess.CalledProcessError as e:
        print(f"[Error] Remote generation failed: {e}")
    finally:
        # 7. Collect Generated Videos
        print("\n=== 5. Collecting Outputs from VM ===")
        local_out = os.path.join(repo_root, "outputs")
        os.makedirs(local_out, exist_ok=True)
        try:
            run_cmd([
                "gcloud", "compute", "scp",
                f"{INSTANCE_NAME}:{REMOTE_HOME}/outputs/*",
                local_out,
                f"--zone={ZONE}"
            ])
            print(f"Outputs successfully saved to {local_out}")
        except subprocess.CalledProcessError:
            print("[Warning] Could not download outputs or no output was generated.")

        # 8. Stop Instance to Save Costs
        if not args.keep_running:
            print("\n=== 6. Stopping Instance to Save Costs ===")
            run_cmd(["gcloud", "compute", "instances", "stop", INSTANCE_NAME, f"--zone={ZONE}"])
            print("Instance stopped.")

    print("\nAll tasks completed successfully!")

if __name__ == "__main__":
    main()
