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

LYRICS="examples/lyrics/lyrics_weight_of_the_world.txt"
ABC_SCORE="examples/scores/weight_of_the_world_part1.abc"
OUTPUT="outputs/weight_of_the_world_celtic_sacred.flac"

# Default style: Adopted Celtic Ethereal Sacred style
STYLE="${1:-celtic ethereal fantasy, sacred and majestic, pure crystal female vocal, delicate irish tin whistle, acoustic harp, acoustic fingerstyle guitar, soaring orchestral strings, timeless folklore, grand emotional anime soundtrack, 74 bpm}"

echo "=========================================================="
echo "=== Running Weight of the World (NieR Automata) Generation ==="
echo "=========================================================="
echo "Style:  ${STYLE}"
echo "Lyrics: ${LYRICS}"
echo "Score:  ${ABC_SCORE}"
echo "Output: ${OUTPUT}"
echo "----------------------------------------------------------"

python3 generate.py \
  --style "${STYLE}" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC_SCORE}" \
  --cot "full" \
  --ode-steps 32 \
  --temperature 0.85 \
  --top-p 0.95 \
  --cfg-scale 1.25 \
  --seed 777 \
  --output "${OUTPUT}"

echo "=== Generation Finished ==="
ls -lh outputs/weight_of_the_world_*.flac
