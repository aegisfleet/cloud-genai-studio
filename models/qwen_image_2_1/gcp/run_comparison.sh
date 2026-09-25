#!/bin/bash
set -e

export PATH="/home/raizi/.local/bin:$PATH"
cd /home/raizi/qwen-image

echo "=========================================================="
echo " Starting Qwen-Image 2.1 Approach A & B Comparison        "
echo "=========================================================="

echo -e "\n>>> [1/2] Executing Approach A: 2K Native + Tiled VAE <<<"
python3 generate.py \
    --approach a \
    --prompt "A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece, intricate lighting" \
    --width 2048 \
    --height 2048 \
    --steps 15 \
    --seed 42 \
    --benchmark \
    --output outputs/qwen_2k_approach_a_tiled.png

echo -e "\n>>> [2/2] Executing Approach B: 2K Native + bitsandbytes Quantization <<<"
python3 generate.py \
    --approach b \
    --prompt "A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece, intricate lighting" \
    --width 2048 \
    --height 2048 \
    --steps 15 \
    --seed 42 \
    --benchmark \
    --output outputs/qwen_2k_approach_b_quant.png

echo "=========================================================="
echo " All generations completed!                               "
echo "=========================================================="
ls -lh outputs/
