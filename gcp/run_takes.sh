#!/bin/bash
set -e
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/../generate.py" ]; then
  cd "${SCRIPT_DIR}/.."
elif [ -f "${SCRIPT_DIR}/generate.py" ]; then
  cd "${SCRIPT_DIR}"
elif [ -d "/home/${USER}/yue2" ]; then
  cd "/home/${USER}/yue2"
fi

LYRICS="examples/lyrics/lyrics_10deg.txt"
[ -f "lyrics_10deg.txt" ] && LYRICS="lyrics_10deg.txt"

ABC="examples/scores/10deg.abc"
[ -f "10deg.abc" ] && ABC="10deg.abc"

# Pattern A base style (Studio Hi-Fi)
STYLE="professional audio mastering, pristine vocal chain, SSL console mix, Neumann U87, analog warmth, wide stereo image, dynamic range, energetic modern J-Rock, powerful passionate female vocal, roaring overdrive electric guitar riffs, expressive guitar solo, punchy driving drums, dynamic slap bass, emotional rich strings and bright piano, explosive anime rock style, rich layered arrangement, full band production, exciting climax, 160 bpm"

echo "================================================================="
echo "Pattern A Parameter Variant Generation Suite on NVIDIA L4 GPU"
echo "Target ABC: ${ABC}"
echo "Base: Standard VAE, ODE Steps 48"
echo "================================================================="

echo ""
echo ">>> [1/3] Take 1: Tight & Stable (temp=0.85, top_p=0.92, seed=100)"
start_1=$(date +%s)
python3 generate.py \
  --style "${STYLE}" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --vae "m-a-p/YuE2-Vae" \
  --ode-steps 48 \
  --temperature 0.85 \
  --top-p 0.92 \
  --seed 100 \
  --output "outputs/10deg_take1_tight.flac"
end_1=$(date +%s)
echo "Take 1 Finished in $((end_1 - start_1)) seconds."

echo ""
echo ">>> [2/3] Take 2: Enhanced Guidance (temp=0.90, cfg=1.3, seed=100)"
start_2=$(date +%s)
python3 generate.py \
  --style "${STYLE}" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --vae "m-a-p/YuE2-Vae" \
  --ode-steps 48 \
  --temperature 0.90 \
  --top-p 0.95 \
  --cfg-scale 1.3 \
  --seed 100 \
  --output "outputs/10deg_take2_guided.flac"
end_2=$(date +%s)
echo "Take 2 Finished in $((end_2 - start_2)) seconds."

echo ""
echo ">>> [3/3] Take 3: Expressive & Dynamic (temp=1.0, cfg=1.2, seed=777)"
start_3=$(date +%s)
python3 generate.py \
  --style "${STYLE}" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --vae "m-a-p/YuE2-Vae" \
  --ode-steps 48 \
  --temperature 1.0 \
  --top-p 0.95 \
  --cfg-scale 1.2 \
  --seed 777 \
  --output "outputs/10deg_take3_expressive.flac"
end_3=$(date +%s)
echo "Take 3 Finished in $((end_3 - start_3)) seconds."

echo ""
echo "================================================================="
echo "All 3 Takes Completed!"
echo "Take 1 (Tight/Stable, temp=0.85): $((end_1 - start_1))s"
echo "Take 2 (Enhanced Guidance, cfg=1.3): $((end_2 - start_2))s"
echo "Take 3 (Expressive, seed=777): $((end_3 - start_3))s"
echo "================================================================="
ls -lh outputs/10deg_take*.flac
