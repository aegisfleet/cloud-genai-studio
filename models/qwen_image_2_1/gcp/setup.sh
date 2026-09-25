#!/bin/bash
set -e

echo "=========================================================="
echo " Setting up Qwen-Image 2.1 Environment on NVIDIA L4 VM    "
echo "=========================================================="

# 1. Setup 24GB Swapfile to protect against RAM spikes when offloading 28GB model
if [ ! -f /swapfile ]; then
    echo "Creating 24GB Swapfile..."
    sudo fallocate -l 24G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=24576
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo "Swapfile created and activated successfully."
fi

# 2. Fix GCP Deep Learning VM ABI conflict with torchaudio/torchvision
sudo pip3 uninstall -y torchaudio torchvision 2>/dev/null || true
pip3 uninstall -y torchaudio torchvision 2>/dev/null || true

# 3. Update pip and install PyTorch/Diffusers packages
echo "Installing latest PyTorch and Diffusers dependencies..."
pip3 install --upgrade pip
pip3 install -q \
    transformers>=4.48.0 \
    accelerate>=1.0.0 \
    sentencepiece \
    protobuf \
    pillow \
    psutil \
    "jinja2>=3.1.0" \
    tqdm

# Install latest diffusers supporting Qwen-Image-2.1
pip3 install -q git+https://github.com/huggingface/diffusers.git

echo "Qwen-Image 2.1 environment is ready!"
