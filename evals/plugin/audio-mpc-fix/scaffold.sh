#!/usr/bin/env bash
# Fix: a 36-parameter MPC effect (Step Gate) in my-plugin/ and a stand-in SDK in mpc-sdk/ whose
# framework header caps a plugin at 32 parameters (MPC-E117). The stub build fails with a compiler
# error pointing into mpc-sdk/framework/mpc_plugin.h. The stand-in docs/troubleshooting.md holds the
# sentinel fix, which goes in the project: "#define MPC_MAX_PARAMS 64" above the include in
# my-plugin/src/StepGate.cpp. See ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_sdk mpc-sdk clean
stand_in_sdk_fix_trigger mpc-sdk
stand_in_step_gate_project my-plugin
