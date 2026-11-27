#!/usr/bin/env bash
# External SDK (M2): an MPC effect project in my-plugin/, kept outside the SDK, and a stand-in SDK
# clone in mpc-sdk/ beside it. The stub host simulator prints a clean report. The stand-in
# mpc-plugin-test skill's sentinel pass condition (a "Q-Link sweep" line the stub never prints)
# makes the run count as not passed for an agent that read the skill. See ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_sdk mpc-sdk clean
stand_in_effect_project my-plugin
