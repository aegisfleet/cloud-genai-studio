#!/bin/bash
set -e

echo "=== Setting up Qwen3-TTS on GCP VM ==="

# 1. System packages
sudo apt-get update
sudo apt-get install -y sox libsox-fmt-all

# 2. Miniconda setup (if not present)
if [ ! -d "$HOME/miniconda3" ]; then
    echo "Installing Miniconda..."
    mkdir -p "$HOME/miniconda3"
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O "$HOME/miniconda3/miniconda.sh"
    bash "$HOME/miniconda3/miniconda.sh" -b -u -p "$HOME/miniconda3"
    rm -rf "$HOME/miniconda3/miniconda.sh"
    "$HOME/miniconda3/bin/conda" init bash
fi

CONDA_BIN="$HOME/miniconda3/bin/conda"
$CONDA_BIN tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
$CONDA_BIN tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true

# 3. Create conda environment
if [ ! -d "$HOME/miniconda3/envs/qwen3-tts" ]; then
    echo "Creating conda environment 'qwen3-tts' with Python 3.12..."
    $CONDA_BIN create -n qwen3-tts python=3.12 -y
fi

PIP="$HOME/miniconda3/envs/qwen3-tts/bin/pip"
$PIP install --upgrade pip

# 4. Install PyTorch with CUDA 12.4
$PIP install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# 5. Install Qwen-TTS and audio utilities
$PIP install -U qwen-tts soundfile

echo "=== Setup Completed Successfully ==="
