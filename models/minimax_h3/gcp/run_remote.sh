#!/bin/bash
set -e

COMFY_DIR="$HOME/ComfyUI"
WORKDIR="$HOME/minimax-h3"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Ensure ComfyUI is up
if ! curl -s http://127.0.0.1:8188/system_stats > /dev/null; then
    echo "[Info] Starting ComfyUI server..."
    nohup python3 "$COMFY_DIR/main.py" --listen 127.0.0.1 --port 8188 > "$HOME/comfyui.log" 2>&1 &
    sleep 5
fi

IMAGE="${1:-$WORKDIR/sample_portrait.jpg}"
AUDIO="${2:-$WORKDIR/sample_japanese_speech.mp3}"
PROMPT="${3:-<Picture 1> <Audio 1> A professional Japanese woman talking naturally and looking directly at the camera.}"
WIDTH="${4:-640}"
HEIGHT="${5:-640}"
LENGTH="${6:-124}"

echo "=== Running MiniMax H3 Generation ==="
python3 "$WORKDIR/generate.py" \
    --image "$IMAGE" \
    --audio "$AUDIO" \
    --prompt "$PROMPT" \
    --width "$WIDTH" \
    --height "$HEIGHT" \
    --length "$LENGTH" \
    --steps 4 \
    --seed 42 \
    --output_dir "$WORKDIR/outputs"

echo "=== Generation Finished ==="
ls -lh "$WORKDIR/outputs/"
