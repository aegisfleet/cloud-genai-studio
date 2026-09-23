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

LYRICS="lyrics_nier_ruins.txt"
[ -f "examples/lyrics/lyrics_nier_ruins.txt" ] && LYRICS="examples/lyrics/lyrics_nier_ruins.txt"

echo "=== Running NieR:Automata City Ruins Style Generation on L4 GPU ==="
python3 generate.py \
  --style "ethereal female vocal, acoustic guitar arpeggio, melancholic piano, sweeping strings, desolate ruin, cinematic NieR Automata style, haunting emotional vocalise, ambient neoclassical, 84 bpm" \
  --lyrics-file "${LYRICS}" \
  --cot "full" \
  --seed 42 \
  --output "outputs/nier_city_ruins.flac"

echo "=== Generation Finished ==="
ls -lh outputs/
