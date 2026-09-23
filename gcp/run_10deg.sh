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

LYRICS="lyrics_10deg.txt"
[ -f "examples/lyrics/lyrics_10deg.txt" ] && LYRICS="examples/lyrics/lyrics_10deg.txt"

ABC="10deg.abc"
[ -f "examples/scores/10deg.abc" ] && ABC="examples/scores/10deg.abc"

echo "=== Running Dynamic & Energetic J-Rock 10deg Song Generation on L4 GPU ==="
python3 generate.py \
  --style "energetic modern J-Rock, powerful passionate female vocal, roaring overdrive electric guitar riffs, expressive guitar solo, punchy driving drums, dynamic slap bass, emotional rich strings and bright piano, explosive anime rock style, rich layered arrangement, full band production, exciting climax, 160 bpm" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --cot "full" \
  --seed 100 \
  --output "outputs/10deg_song.flac"

echo "=== Generation Finished ==="
ls -lh outputs/
