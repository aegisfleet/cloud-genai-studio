#!/bin/bash
set -e

COMFY_DIR="$HOME/ComfyUI"
WORKDIR="$HOME/minimax-h3"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Ensure ComfyUI is up
if ! curl -s http://127.0.0.1:8188/system_stats > /dev/null; then
    echo "[Info] Starting ComfyUI server..."
    pkill -f 'python3 main.py' || true
    nohup python3 "$COMFY_DIR/main.py" --listen 127.0.0.1 --port 8188 > "$HOME/comfyui.log" 2>&1 &
fi

echo "[Info] Waiting for ComfyUI to become ready on http://127.0.0.1:8188..."
READY=false
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8188/system_stats > /dev/null; then
        echo "[Info] ComfyUI is UP and responding! (attempt $i)"
        READY=true
        break
    fi
    echo "[Info] Waiting for ComfyUI... (attempt $i/30)"
    sleep 3
done

if [ "$READY" != "true" ]; then
    echo "[Error] ComfyUI failed to respond in time! Dumping comfyui.log:"
    tail -n 60 "$HOME/comfyui.log" || true
    exit 1
fi

IMAGE="${1:-$WORKDIR/sample_portrait.jpg}"
AUDIO="${2:-}"
PROMPT="${3:-}"
PROMPT_FILE="${4:-$WORKDIR/prompt.txt}"
WIDTH="${5:-640}"
HEIGHT="${6:-640}"
LENGTH="${7:-360}"

ARGS=(--image "$IMAGE" --width "$WIDTH" --height "$HEIGHT" --length "$LENGTH" --steps 4 --seed 42 --output_dir "$WORKDIR/outputs")

if [ -n "$AUDIO" ] && [ -f "$AUDIO" ]; then
    ARGS+=(--audio "$AUDIO")
fi

if [ -f "$PROMPT_FILE" ]; then
    ARGS+=(--prompt_file "$PROMPT_FILE")
elif [ -n "$PROMPT" ]; then
    ARGS+=(--prompt "$PROMPT")
fi

echo "=== Running MiniMax H3 Generation ==="
echo "Arguments: ${ARGS[@]}"
python3 "$WORKDIR/generate.py" "${ARGS[@]}"

echo "=== Generation Finished ==="
ls -lh "$WORKDIR/outputs/"
