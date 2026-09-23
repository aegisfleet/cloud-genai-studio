#!/bin/bash
set -e
cd /home/raizi/yue2

echo "=== Verifying Imports ==="
python3 -c "import torch; from transformers import PreTrainedModel; from yue2 import YuE2Pipeline; print('All core modules imported successfully! PyTorch:', torch.__version__, 'CUDA:', torch.cuda.is_available())"

echo "=== Running YuE2 Music Generation on L4 GPU ==="
python3 generate.py --style "J-Pop, emotional female vocal, dynamic piano, upbeat anime opening" --output "outputs/cloud_song.flac"

echo "=== Generation Completed ==="
ls -lh outputs/
