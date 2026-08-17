#!/bin/bash
# Run the five h3edit demos. Sequential on purpose: two H3 renders competing for MPS on this box
# took a 40 s/it render to 255 s/it. Skips anything already produced, so it resumes cleanly.
set -u
cd "$(dirname "$0")"
mkdir -p out

DEMOS="
can:can_scene-s42:can_label-s84:16:9
gable:gable_scene-s77:gable_mural-s79:16:9
neon:storefront_scene-s42:neon_sign-s42:16:9
tattoo:arm_scene-s77:tattoo_flash-s42:16:9
book:book_scene-s77:book_cover-s42:16:9
"

for entry in $DEMOS; do
  IFS=: read -r name scene art ar1 ar2 <<< "$entry"
  ar="${ar1}:${ar2}"
  if [ -f "out/${name}.png" ]; then echo "skip  $name"; continue; fi
  echo "=== $name   $scene + $art   ar $ar"
  h3edit "$(cat "prompts/${name}.txt")" \
    -r "refs/${scene}.png" -r "refs/${art}.png" \
    --ar "$ar" --name "demo_${name}" -o "out/${name}.png" --wait 2>&1 | tail -2
done

echo "=== done"
ls -la out/
