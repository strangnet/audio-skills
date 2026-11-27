#!/usr/bin/env bash
# New effect outside the SDK: an empty repo for a new MPC effect in my-plugin/ (a README and a
# .gitignore, no code yet) and a stand-in SDK clone in mpc-sdk/ beside it. The prompt asks what the
# plugin must have and keep to before any code is written, so the answer must cover every hard rule
# audio-mpc states. See ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_sdk mpc-sdk clean

mkdir -p my-plugin
cat > my-plugin/README.md <<'MD'
# Shimmer

A pitch-shifted reverb for Akai MPC hardware, by Example Audio. Kept in its own repository and
built with the MPC SDK's tools from outside the SDK. No code yet.
MD
cat > my-plugin/.gitignore <<'TXT'
build/
dist/
TXT
