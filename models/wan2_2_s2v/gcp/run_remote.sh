#!/usr/bin/env bash
set -e

cd ~/minimax-h3

# Set memory allocator optimizations
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Always restart ComfyUI to ensure fresh GPU memory state
echo "[Info] Restarting ComfyUI server to ensure clean GPU VRAM..."
pkill -9 -f "main.py" || true
sleep 2

nohup python3 ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188 > ~/comfyui.log 2>&1 &
for i in {1..30}; do
    if curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
        echo "[Info] ComfyUI server is online and ready."
        break
    fi
    sleep 2
done

IMAGE="$1"
AUDIO="$2"
OUTPUT="$3"
PROMPT="${4:-A person talking and singing naturally, synchronized with the audio, high quality}"
EXTRA_ARGS="${@:5}"

echo "=== Executing Wan2.2-S2V Audio-Driven Generation on GCP VM ==="
echo "Image : $IMAGE"
echo "Audio : $AUDIO"
echo "Output: $OUTPUT"
echo "Prompt: $PROMPT"
echo "Extra : $EXTRA_ARGS"

python3 generate.py \
    --image "$IMAGE" \
    --audio "$AUDIO" \
    --output "$OUTPUT" \
    --prompt "$PROMPT" \
    $EXTRA_ARGS

echo "=== Wan2.2-S2V Execution Finished Successfully ==="
