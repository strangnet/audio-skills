#!/usr/bin/env bash
# First build: an MPC effect project in my-plugin/ and a stand-in SDK clone in mpc-sdk/ that has
# never been built: no tool cache (.sdk-tools/), so no host simulator and no zig, and its top folder
# is read-only. The stub build tool tries to create .sdk-tools/ and stops with the uncaught
# PermissionError the real tools/build.py gives. See ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_sdk mpc-sdk clean
stand_in_effect_project my-plugin
stand_in_sdk_first_build mpc-sdk
