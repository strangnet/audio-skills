#!/usr/bin/env bash
# Install asked: an MPC effect project in my-plugin/, kept outside the SDK, with finished build output
# from the stand-in SDK's stub build tool, and a stand-in SDK clone in mpc-sdk/ beside it. The
# stand-in mpc-plugin-deploy skill's "MPC-SAFE-COPY" check is the sentinel: it shows the agent read
# that skill by path. See ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_sdk mpc-sdk clean
stand_in_effect_project my-plugin
stand_in_built_project mpc-sdk my-plugin
