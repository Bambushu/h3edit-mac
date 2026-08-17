#!/bin/bash
# Render the reference stills for the h3edit demos, one per spec in specs/.
#
# One `ideogram render` invocation PER IMAGE: at DEFAULT_20 the M5 accumulates MPS memory across
# seeds inside a single process and the second frame stalls then SIGTERMs. A fresh process
# releases it.
#
# Seed and size come from the spec itself (the caption JSON carries neither), so bumping a seed
# after a bad roll means editing one file, not this script. Anything already in refs/ is skipped,
# so re-running after a rejection only renders what is missing -- reject by MOVING the file to
# refs/rejected/, which keeps the failure auditable and stops the skip-glob matching it.
#
# A refusal is not a failure: the engine renames the card to REFUSED-*.png and exits 0. Any spec
# listed in ANTI_REFUSAL goes through the escalation path (lexicon -> seed ladder -> bait-CFG,
# VLM-judge validated), which ignores --seed and always starts at 42.
set -u
cd "$(dirname "$0")"
mkdir -p refs refs/rejected

ANTI_REFUSAL="gable_mural"

for spec in specs/*.yaml; do
  name=$(basename "$spec" .yaml)
  if compgen -G "refs/${name}-*.png" > /dev/null; then
    echo "skip  $name"; continue
  fi
  seed=$(awk '/^seed:/{print $2}' "$spec")
  size=$(awk '/^size:/{print $2}' "$spec")
  if [[ " $ANTI_REFUSAL " == *" $name "* ]]; then
    echo "=== $name  $size  (anti-refusal escalation)"
    ideogram render "caps/${name}.json" --anti-refusal auto --size "$size" --out refs 2>&1 | tail -2
  else
    echo "=== $name  $size  seed $seed"
    ideogram render "caps/${name}.json" --seed "$seed" --preset V4_DEFAULT_20 --size "$size" --out refs 2>&1 | tail -2
  fi
  compgen -G "refs/REFUSED*${name}*" > /dev/null && echo "!!! $name REFUSED"
done

echo "=== done"
ls refs/*.png 2>/dev/null | grep -v sheet
