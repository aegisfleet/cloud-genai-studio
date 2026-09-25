#!/usr/bin/env bash
set -e

echo "=== [1/6] Setting up Swap (24GB) ==="
if [ ! -f /swapfile ]; then
    sudo fallocate -l 24G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=24576
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi
free -h

echo "=== [2/6] Configuring Environment & System Packages ==="
sudo apt-get update -y
sudo apt-get install -y ffmpeg git git-lfs aria2 curl jq

# Ensure local bin is on PATH cleanly
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi
export PATH="$HOME/.local/bin:$PATH"

pip3 install --upgrade pip setuptools wheel
pip3 install huggingface_hub aiohttp requests tqdm

echo "=== [3/6] Setting up ComfyUI (Latest Master) ==="
cd ~
if [ ! -d ~/ComfyUI ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
else
    cd ~/ComfyUI
    git pull || true
fi
cd ~/ComfyUI
pip3 install -r requirements.txt

# Create model directories for Wan2.2-S2V
mkdir -p models/diffusion_models models/text_encoders models/audio_encoders models/vae models/loras models/embeddings

echo "=== [4/6] Downloading Wan2.2-S2V Models (~23.5GB total via aria2c) ==="
# Download function using aria2c for maximum speed
download_model() {
    local url="$1"
    local dir="$2"
    local filename="$3"
    local dest="$dir/$filename"

    if [ -f "$dest" ] && [ $(stat -c%s "$dest" 2>/dev/null || stat -f%z "$dest") -gt 10485760 ]; then
        echo "Already downloaded: $dest ($(du -h "$dest" | cut -f1))"
    else
        echo "Downloading $filename to $dir ..."
        mkdir -p "$dir"
        aria2c -x 8 -s 8 -k 1M --file-allocation=none --dir="$dir" --out="$filename" "$url"
    fi
}

# 1. Diffusion Model (Wan2.2 S2V 14B FP8 scaled, ~15.2GB)
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_fp8_scaled.safetensors" \
    "$HOME/ComfyUI/models/diffusion_models" \
    "wan2.2_s2v_14B_fp8_scaled.safetensors"

# 2. Text Encoder (UMT5 XXL FP8 scaled, ~6.3GB)
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
    "$HOME/ComfyUI/models/text_encoders" \
    "umt5_xxl_fp8_e4m3fn_scaled.safetensors"

# 3. Audio Encoder (Wav2Vec2 Large English FP16, ~601MB)
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors" \
    "$HOME/ComfyUI/models/audio_encoders" \
    "wav2vec2_large_english_fp16.safetensors"

# 4. VAE (Wan 2.1 VAE, ~242MB)
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" \
    "$HOME/ComfyUI/models/vae" \
    "wan_2.1_vae.safetensors"

# 5. Lightning 4-step LoRA (~1.14GB)
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors" \
    "$HOME/ComfyUI/models/loras" \
    "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors"

echo "=== [5/6] Verifying Downloaded Models ==="
ls -lh ~/ComfyUI/models/diffusion_models/
ls -lh ~/ComfyUI/models/text_encoders/
ls -lh ~/ComfyUI/models/audio_encoders/
ls -lh ~/ComfyUI/models/vae/
ls -lh ~/ComfyUI/models/loras/

echo "=== [6/6] Launching ComfyUI Server in Background ==="
# Kill any existing server
pkill -f "main.py --listen" || true
sleep 2

nohup python3 ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188 > ~/comfyui.log 2>&1 &
sleep 5

# Verify server response
curl -s http://127.0.0.1:8188/system_stats | jq . || echo "ComfyUI server starting up..."

echo "=== Wan2.2-S2V Setup Completed Successfully ==="
