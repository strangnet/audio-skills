#!/usr/bin/env bash
# Inside a checkout: the working folder is itself a stand-in SDK checkout (its tools/ holds the stub
# build tool), with an MPC effect project in its plugins/ folder. Akai's skills lead here, so
# audio-mpc shouldn't fire. The checkout's own .claude/skills aren't discovered by the eval runner
# (mpc task 01, smoke finding a), so Akai's skills can only be read as files. See
# ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_sdk . clean
stand_in_effect_project plugins/Grit
cat > plugins/Grit/README.md <<'MD'
# Grit

A soft-clip saturator for Akai MPC hardware, made in this SDK's plugins/ folder.
MD
