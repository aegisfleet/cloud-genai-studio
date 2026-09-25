#!/bin/bash
set -e

PROMPT="${1:-A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece, intricate lighting}"
WIDTH="${2:-2048}"
HEIGHT="${3:-2048}"
STEPS="${4:-25}"
OUTPUT="${5:-outputs/qwen_image_2k.png}"

echo "Running Qwen-Image 2.1 Generation..."
echo "Prompt: $PROMPT"
echo "Resolution: ${WIDTH}x${HEIGHT}"
echo "Steps: $STEPS"
echo "Output: $OUTPUT"

python3 generate.py \
    --prompt "$PROMPT" \
    --width "$WIDTH" \
    --height "$HEIGHT" \
    --steps "$STEPS" \
    --benchmark \
    --output "$OUTPUT"
