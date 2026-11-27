#!/usr/bin/env bash
# SDK changed: an MPC effect project in my-plugin/ and a stand-in SDK in mpc-sdk/ whose documents
# (docs/supported-devices.md, docs/install-and-test.md) name MPC OS 3.14.2 as the minimum, where the
# skill's summary, checked against the real SDK at e78bad5, says 3.10.1. See ../_shared/stand-in-sdk.sh.
set -euo pipefail
# shellcheck source=../_shared/stand-in-sdk.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
stand_in_sdk mpc-sdk clean
stand_in_effect_project my-plugin
stand_in_sdk_changed mpc-sdk 3.14.2
