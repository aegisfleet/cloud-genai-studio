#!/bin/bash
set -e

echo "=== [1/4] Setting up ComfyUI and Dependencies for MiniMax H3 ==="
sudo apt-get update -y
sudo apt-get install -y git python3-pip python3-venv ffmpeg

COMFY_DIR="$HOME/ComfyUI"
if [ ! -d "$COMFY_DIR" ]; then
    echo "Cloning ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi

cd "$COMFY_DIR"
pip install --upgrade pip
pip install -r requirements.txt
pip install huggingface_hub torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu124
pip install ninja flash-attn --no-build-isolation || true

echo "=== [2/4] Downloading MiniMax H3 Quantized Models ==="
# Python script to download models into ComfyUI/models/
python3 - << 'EOF'
import os
from huggingface_hub import hf_hub_download

repo = "Comfy-Org/MiniMax-H3"
comfy_home = os.path.expanduser("~/ComfyUI")

models_to_download = [
    ("vae/minimax_h3_video_vae_int8_convrot.safetensors", "models/vae/minimax_h3_video_vae_int8_convrot.safetensors"),
    ("vae/minimax_h3_audio_vae_fp32.safetensors", "models/vae/minimax_h3_audio_vae_fp32.safetensors"),
    ("diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors", "models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"),
    ("text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"),
    ("loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors", "models/loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"),
]

for remote_file, local_rel in models_to_download:
    dest = os.path.join(comfy_home, local_rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 1024*1024:
        print(f"Already exists: {dest} ({os.path.getsize(dest)/(1024*1024):.1f} MB)")
        continue
    print(f"Downloading {remote_file} -> {dest} ...")
    hf_hub_download(
        repo_id=repo,
        filename=remote_file,
        local_dir=comfy_home,
    )
    # symlink if needed
    src = os.path.join(comfy_home, remote_file)
    if os.path.exists(src) and not os.path.exists(dest):
        os.symlink(src, dest)
print("MiniMax H3 models ready!")
EOF

echo "=== [3/4] Ensuring Models are Linked in models/ Directory ==="
mkdir -p "$COMFY_DIR/models/diffusion_models" "$COMFY_DIR/models/text_encoders" "$COMFY_DIR/models/vae" "$COMFY_DIR/models/loras"
for f in "$COMFY_DIR"/diffusion_models/*; do [ -f "$f" ] && ln -sf "$f" "$COMFY_DIR/models/diffusion_models/" || true; done
for f in "$COMFY_DIR"/text_encoders/*; do [ -f "$f" ] && ln -sf "$f" "$COMFY_DIR/models/text_encoders/" || true; done
for f in "$COMFY_DIR"/vae/*; do [ -f "$f" ] && ln -sf "$f" "$COMFY_DIR/models/vae/" || true; done
for f in "$COMFY_DIR"/loras/*; do [ -f "$f" ] && ln -sf "$f" "$COMFY_DIR/models/loras/" || true; done

echo "=== [4/4] Starting ComfyUI Server ==="
pkill -f 'python3 main.py' || true
nohup python3 "$COMFY_DIR/main.py" --listen 127.0.0.1 --port 8188 > "$HOME/comfyui.log" 2>&1 &
echo "ComfyUI running in background. Waiting for startup..."
sleep 5
curl -s http://127.0.0.1:8188/system_stats || true
echo "Setup complete!"
