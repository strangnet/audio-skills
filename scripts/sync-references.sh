#!/usr/bin/env bash
# Vendors shared reference files into each skill, so every skill stays
# self-contained when installed or copied on its own.
#
# Each folder under references/ (e.g. references/languages/) is a shared set.
# A skill opts in to a set by having a folder of the same name under its own
# references/ (e.g. skills/tdd-cycle/references/languages/).
#
#   scripts/sync-references.sh          copy every shared set into the skills that opt in
#   scripts/sync-references.sh --check  exit 1 if any skill's copy has drifted (for CI)
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
mode=${1:-sync}
status=0

for src in "$root"/references/*/; do
  src=${src%/}
  set_name=$(basename "$src")
  for dest in "$root"/skills/*/references/"$set_name"; do
    [ -d "$dest" ] || continue
    rel=${dest#"$root"/}
    if [ "$mode" = "--check" ]; then
      if ! diff -r -q "$src" "$dest" >/dev/null; then
        echo "out of sync: $rel (run scripts/sync-references.sh)"
        status=1
      fi
    else
      # Remove copies of files that no longer exist at the source.
      for f in "$dest"/*.md; do
        [ -e "$f" ] || continue
        [ -e "$src/$(basename "$f")" ] || rm "$f"
      done
      cp "$src"/*.md "$dest"/
      echo "synced $rel"
    fi
  done
done

exit "$status"
