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

echo "=== Running MiniMax H3 Generation ==="
echo "Arguments: $@"
python3 "$WORKDIR/generate.py" "$@"

echo "=== Generation Finished ==="
ls -lh "$WORKDIR/outputs/"
