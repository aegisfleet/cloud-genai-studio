#!/bin/bash
set -e

echo "=========================================================="
echo " Setting up Qwen-Image 2.1 Environment on NVIDIA L4 VM    "
echo "=========================================================="

# 1. Setup 24GB Swapfile to protect against RAM spikes (persist in /etc/fstab)
if [ ! -f /swapfile ]; then
    echo "Creating 24GB Swapfile..."
    sudo fallocate -l 24G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=24576
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    sudo grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "Swapfile created, activated, and registered in /etc/fstab."
else
    sudo swapon /swapfile 2>/dev/null || true
    sudo grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 2. Fix GCP Deep Learning VM ABI conflict with torchaudio
sudo pip3 uninstall -y torchaudio 2>/dev/null || true
pip3 uninstall -y torchaudio 2>/dev/null || true

# 3. Ensure matched torchvision for PyTorch 2.9 (cu129)
pip3 install -q torchvision==0.24.1+cu129 --extra-index-url https://download.pytorch.org/whl/cu129

# 4. Update pip and install PyTorch/Diffusers dependencies
echo "Installing dependencies (bitsandbytes, transformers, diffusers, jinja2)..."
pip3 install --upgrade pip
pip3 install -q \
    transformers>=4.48.0 \
    accelerate>=1.0.0 \
    bitsandbytes>=0.43.3 \
    "jinja2>=3.1.0" \
    sentencepiece \
    protobuf \
    pillow \
    psutil \
    tqdm

# Install latest diffusers supporting Qwen-Image-2.1
pip3 install -q git+https://github.com/huggingface/diffusers.git

echo "Qwen-Image 2.1 environment is fully configured and ready!"
