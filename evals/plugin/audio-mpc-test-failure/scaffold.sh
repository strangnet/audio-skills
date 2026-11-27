#!/usr/bin/env bash
# Test failure: an MPC effect project in my-plugin/ and a stand-in SDK in mpc-sdk/ whose stub host
# simulator prints one FAIL line (NaN or Inf output in the main render) and exits 1. The build and
# its validation pass. See ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_sdk mpc-sdk fail
stand_in_effect_project my-plugin
