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

# Studio-grade audio mastering style prompt
STYLE="professional audio mastering, pristine vocal chain, SSL console mix, Neumann U87, analog warmth, wide stereo image, dynamic range, energetic modern J-Rock, powerful passionate female vocal, roaring overdrive electric guitar riffs, expressive guitar solo, punchy driving drums, dynamic slap bass, emotional rich strings and bright piano, explosive anime rock style, rich layered arrangement, full band production, exciting climax, 160 bpm"

echo "================================================================="
echo "YuE2 Quality Comparison Suite on NVIDIA L4 GPU"
echo "Target ABC: ${ABC}"
echo "Seed: 100"
echo "================================================================="

echo ""
echo ">>> [1/3] Pattern A: Studio Hi-Fi Tags + ODE Steps 48 (Standard VAE)"
start_a=$(date +%s)
python3 generate.py \
  --style "${STYLE}" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --vae "m-a-p/YuE2-Vae" \
  --ode-steps 48 \
  --cot "full" \
  --seed 100 \
  --output "outputs/10deg_pattern_a_hifi.flac"
end_a=$(date +%s)
echo "Pattern A Finished in $((end_a - start_a)) seconds."

echo ""
echo ">>> [2/3] Pattern B: Legacy VAE (YuE2-Vae-legacy) + ODE Steps 48"
start_b=$(date +%s)
python3 generate.py \
  --style "${STYLE}" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --vae "m-a-p/YuE2-Vae-legacy" \
  --ode-steps 48 \
  --cot "full" \
  --seed 100 \
  --output "outputs/10deg_pattern_b_legacy.flac"
end_b=$(date +%s)
echo "Pattern B Finished in $((end_b - start_b)) seconds."

echo ""
echo ">>> [3/3] Pattern C: Extreme Hi-Fi (Standard VAE + ODE Steps 64)"
start_c=$(date +%s)
python3 generate.py \
  --style "${STYLE}" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --vae "m-a-p/YuE2-Vae" \
  --ode-steps 64 \
  --cot "full" \
  --seed 100 \
  --output "outputs/10deg_pattern_c_extreme.flac"
end_c=$(date +%s)
echo "Pattern C Finished in $((end_c - start_c)) seconds."

echo ""
echo "================================================================="
echo "All Patterns Completed!"
echo "Pattern A (ODE 48 + Standard VAE): $((end_a - start_a))s"
echo "Pattern B (ODE 48 + Legacy VAE):   $((end_b - start_b))s"
echo "Pattern C (ODE 64 + Standard VAE): $((end_c - start_c))s"
echo "================================================================="
ls -lh outputs/10deg_pattern_*.flac
