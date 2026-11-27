#!/usr/bin/env bash
# Routing to audio-parameters: a released MPC saturator effect kept in my-plugin/, outside any SDK
# checkout. Version 1.0.0 shipped with four parameters (output at index 0, drive, tone, mix) and no
# Knob FX mapping. The prompt asks to move Mix to the front and to add the Knob FX mapping, so the
# advice belongs to audio-parameters; audio-mpc may fire too but adds only its one-line rules.
# No SDK or toolchain is needed.
set -euo pipefail
mkdir -p my-plugin/src

cat > my-plugin/CHANGELOG.md <<'MD'
# Changelog

## 1.0.0 (released)

- First release on the MPC.
MD

cat > my-plugin/plugin.json <<'JSON'
{
  "name": "Crunch",
  "manufacturer": "Example Audio",
  "version": "1.0.0",
  "format": "vst2",
  "kind": "effect",
  "uid": "ExCr",
  "numInputs": 2,
  "numOutputs": 2,
  "file32": "VST/crunch-arm32.so",
  "file64": "VST/crunch-arm64.so"
}
JSON

cat > my-plugin/src/Crunch.cpp <<'CPP'
// Crunch: a saturator for the MPC. Signal flow: drive -> soft clip -> tone (one-pole low-pass)
// -> dry/wet mix -> output trim.
#include "mpc_plugin.h"

#include <cmath>

class Crunch : public mpc::Plugin {
public:
    Crunch() : mpc::Plugin(makeInfo()) {
        addParam(mpc::floatParam("output", "Output", -24, 6, 0, "dB", 1));
        addParam(mpc::floatParam("drive", "Drive", 0, 36, 12, "dB", 1));
        addParam(mpc::floatParam("tone", "Tone", 500, 18000, 8000, "Hz", 0));
        addParam(mpc::floatParam("mix", "Mix", 0, 100, 100, "%", 0));
        addProgram("Init", {0.0f, 12.0f, 8000.0f, 100.0f});
        addProgram("Warm", {-3.0f, 18.0f, 3000.0f, 70.0f});
    }

    void process(mpc::ProcessContext& ctx) override;  // DSP omitted from this excerpt

private:
    static mpc::PluginInfo makeInfo() {
        mpc::PluginInfo info;
        info.name = "Crunch";
        info.vendor = "Example Audio";
        info.uniqueId = MPC_FOURCC('E', 'x', 'C', 'r');
        info.isInstrument = false;
        info.numInputs = 2;
        info.numOutputs = 2;
        return info;
    }
};

MPC_PLUGIN_ENTRY(Crunch)
CPP
