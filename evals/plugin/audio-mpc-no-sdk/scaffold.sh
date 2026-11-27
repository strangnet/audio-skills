#!/usr/bin/env bash
# No SDK: an MPC effect project in my-plugin/ and no SDK anywhere in the working folder. The prompt
# names none, and $MPC_SDK is unset in the run. See ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_effect_project my-plugin
