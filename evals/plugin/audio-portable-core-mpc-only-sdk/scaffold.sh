#!/usr/bin/env bash
# A stand-in for an Akai MPC Plugin SDK checkout: the SDK's top-level layout, an empty
# tools/ folder, and one MPC-only plugin project. No SDK files are included.
set -euo pipefail
mkdir -p tools framework plugins/EchoBox/src
touch tools/.keep framework/.keep

cat > README.md <<'MD'
# MPC Plugin SDK

Build insert effects and instruments for Akai MPC standalone hardware.
Projects live in `plugins/<Name>/` and are built with `python tools/build.py plugins/<Name>`.
MD

cat > plugins/EchoBox/plugin.json <<'JSON'
{
  "name": "EchoBox",
  "manufacturer": "Example",
  "version": "1.0.0",
  "format": "vst2",
  "kind": "effect",
  "uid": "ExEb",
  "numInputs": 2,
  "numOutputs": 2,
  "knobs": [ { "parameter": 1, "label": "Time" }, { "parameter": 2, "label": "Feedback" } ]
}
JSON

cat > plugins/EchoBox/src/EchoBox.cpp <<'CPP'
// EchoBox: an MPC insert effect.
#include "mpc_plugin.h"

class EchoBox : public mpc::Plugin {
public:
    EchoBox() : mpc::Plugin(info()) {
        addParam(mpc::floatParam("output", "Output", -12, 12, 0, "dB", 1));
        addParam(mpc::floatParam("time", "Time", 10, 1000, 250, "ms", 0));
        addParam(mpc::floatParam("feedback", "Feedback", 0, 95, 40, "%", 0));
    }
    void process(mpc::ProcessContext& ctx) override { (void)ctx; }
};

MPC_PLUGIN_ENTRY(EchoBox)
CPP
