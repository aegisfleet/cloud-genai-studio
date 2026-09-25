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
pip install huggingface_hub "torch>=2.4.0" torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu124
# 豕ｨ: flash-attn 縺ｮ繧ｽ繝ｼ繧ｹ繧ｳ繝ｳ繝代う繝ｫ縺ｯ荳崎ｦ・ｼ・yTorch 2.9+ 繝阪う繝・ぅ繝・SDPA 縺・FlashAttention2 莠呈鋤縺ｧ蜍穂ｽ懊☆繧九◆繧・ｼ・
echo "=== [2/4] Downloading MiniMax H3 Quantized Models ==="
python3 - << 'EOF'
import os
import shutil
from huggingface_hub import hf_hub_download

repo = "Comfy-Org/MiniMax-H3"
comfy_home = os.path.expanduser("~/ComfyUI")

models_to_download = [
    ("vae/minimax_h3_video_vae_int8_convrot.safetensors", "models/vae/minimax_h3_video_vae_int8_convrot.safetensors"),
    ("vae/minimax_h3_audio_vae_fp32.safetensors", "models/vae/minimax_h3_audio_vae_fp32.safetensors"),
    ("diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors", "models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors"),
    ("text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"),
    ("loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors", "models/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"),
]

for remote_file, local_rel in models_to_download:
    dest = os.path.join(comfy_home, local_rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 1024 * 1024:
        print(f"[Exists] {dest} ({os.path.getsize(dest)/(1024*1024):.1f} MB)")
        continue
    if os.path.islink(dest) or os.path.lexists(dest):
        os.remove(dest)
    print(f"[Resolving] {remote_file} -> {dest} ...")
    downloaded_path = hf_hub_download(
        repo_id=repo,
        filename=remote_file,
    )
    real_path = os.path.realpath(downloaded_path)
    if not os.path.exists(dest):
        try:
            os.link(real_path, dest)
        except OSError:
            shutil.copy2(real_path, dest)
    print(f"[Ready] {dest} -> {real_path} ({os.path.getsize(dest)/(1024*1024):.1f} MB)")

print("MiniMax H3 Ref2VA models download complete!")
EOF

echo "=== [3/4] Verifying Model Files ==="
ls -lh "$COMFY_DIR/models/diffusion_models/"
ls -lh "$COMFY_DIR/models/text_encoders/"
ls -lh "$COMFY_DIR/models/vae/"
ls -lh "$COMFY_DIR/models/loras/"

echo "=== [4/4] Starting ComfyUI Server ==="
pkill -f 'python3 main.py' || true
nohup python3 "$COMFY_DIR/main.py" --listen 127.0.0.1 --port 8188 > "$HOME/comfyui.log" 2>&1 &
echo "ComfyUI running in background. Waiting for startup..."
sleep 8
curl -s http://127.0.0.1:8188/system_stats || true
echo "Setup complete!"
