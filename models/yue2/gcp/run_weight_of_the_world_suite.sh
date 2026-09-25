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
ABC="examples/scores/weight_of_the_world_part1.abc"

echo "================================================================="
echo "=== Weight of the World (Quiet & Grand Suite) on NVIDIA L4 ==="
echo "Target ABC: ${ABC}"
echo "Lyrics:     ${LYRICS}"
echo "================================================================="

echo ""
echo ">>> [1/3] Take 1: Ambient Grand Cathedral (Temp=0.85, CFG=1.30, Seed=42)"
echo "Style: Ethereal Ambient Cinematic, Cathedral Choir & Lush Strings"
start_1=$(date +%s)
python3 generate.py \
  --style "ethereal ambient cinematic, serene and grand, hauntingly beautiful female vocal, delicate acoustic guitar arpeggios, lonely melancholic piano, distant cathedral choir, sweeping lush strings, deep orchestral resonance, desolate ruins, majestic emotional climax, 74 bpm" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --cot "full" \
  --ode-steps 32 \
  --temperature 0.85 \
  --top-p 0.95 \
  --cfg-scale 1.30 \
  --seed 42 \
  --output "outputs/weight_of_the_world_ambient_grand.flac"
end_1=$(date +%s)
echo "Take 1 Completed in $((end_1 - start_1))s"

echo ""
echo ">>> [2/3] Take 2: Neoclassical Post-Rock Swell (Temp=0.88, CFG=1.30, Seed=100)"
echo "Style: Neoclassical Post-Rock, Fragile to Soaring, Upright Piano & Cello"
start_2=$(date +%s)
python3 generate.py \
  --style "neoclassical post-rock, vast dynamic range, fragile whispery female vocal building into powerful soaring high notes, intimate upright piano, melancholic cello solo, explosive soaring orchestral strings, celestial atmosphere, epic emotional swell, 74 bpm" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --cot "full" \
  --ode-steps 32 \
  --temperature 0.88 \
  --top-p 0.95 \
  --cfg-scale 1.30 \
  --seed 100 \
  --output "outputs/weight_of_the_world_neoclassical.flac"
end_2=$(date +%s)
echo "Take 2 Completed in $((end_2 - start_2))s"

echo ""
echo ">>> [3/3] Take 3: Celtic Ethereal Sacred (Temp=0.85, CFG=1.25, Seed=777)"
echo "Style: Celtic Ethereal Fantasy, Whistle, Harp, Sacred Grandeur"
start_3=$(date +%s)
python3 generate.py \
  --style "celtic ethereal fantasy, sacred and majestic, pure crystal female vocal, delicate irish tin whistle, acoustic harp, acoustic fingerstyle guitar, soaring orchestral strings, timeless folklore, grand emotional anime soundtrack, 74 bpm" \
  --lyrics-file "${LYRICS}" \
  --abc-file "${ABC}" \
  --cot "full" \
  --ode-steps 32 \
  --temperature 0.85 \
  --top-p 0.95 \
  --cfg-scale 1.25 \
  --seed 777 \
  --output "outputs/weight_of_the_world_celtic_sacred.flac"
end_3=$(date +%s)
echo "Take 3 Completed in $((end_3 - start_3))s"

echo ""
echo "================================================================="
echo "All 3 Quiet & Grand Takes Finished Successfully!"
echo "Take 1 (Ambient Grand): $((end_1 - start_1))s"
echo "Take 2 (Neoclassical Swell): $((end_2 - start_2))s"
echo "Take 3 (Celtic Sacred): $((end_3 - start_3))s"
echo "================================================================="
ls -lh outputs/weight_of_the_world_*.flac
