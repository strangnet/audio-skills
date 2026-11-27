#!/usr/bin/env bash
# Routing to audio-portable-core: an MPC chorus effect kept in its own repo under mpc/, outside any
# SDK checkout, with its DSP written inside process() against the SDK's mpc:: types. The prompt
# asks how to share that DSP with a new JUCE wrapper, so the advice belongs to audio-portable-core;
# audio-mpc may fire too but only names it. No SDK or toolchain is needed.
set -euo pipefail
mkdir -p mpc/src

cat > README.md <<'MD'
# Swirl

A stereo chorus. The MPC plugin is in `mpc/`; a desktop version (JUCE: VST3, AU, CLAP) is planned.
MD

cat > mpc/plugin.json <<'JSON'
{
  "name": "Swirl",
  "manufacturer": "Example Audio",
  "version": "1.0.0",
  "format": "vst2",
  "kind": "effect",
  "uid": "ExSw",
  "numInputs": 2,
  "numOutputs": 2,
  "shortName": "Swirl",
  "knobs": [
    { "parameter": 1, "label": "Rate" },
    { "parameter": 2, "label": "Depth" },
    { "parameter": 3, "label": "Mix" }
  ],
  "shiftKnobs": [
    { "parameter": 0, "label": "Output" }
  ],
  "file32": "VST/swirl-arm32.so",
  "file64": "VST/swirl-arm64.so"
}
JSON

cat > mpc/src/Swirl.cpp <<'CPP'
// Swirl: a stereo chorus for the MPC. Signal flow: input -> modulated delay (LFO 90 degrees apart
// per channel) -> dry/wet mix -> output trim. The DSP lives in process().
#include "mpc_plugin.h"

#include <cmath>
#include <vector>

class Swirl : public mpc::Plugin {
public:
    Swirl() : mpc::Plugin(makeInfo()) {
        addParam(mpc::floatParam("output", "Output", -24, 6, 0, "dB", 1));
        addParam(mpc::floatParam("rate", "Rate", 0.05f, 5, 0.6f, "Hz", 2));
        addParam(mpc::floatParam("depth", "Depth", 0, 10, 3, "ms", 1));
        addParam(mpc::floatParam("mix", "Mix", 0, 100, 50, "%", 0));
    }

    void prepare(double sampleRate, int /*maxBlockSize*/) override {
        sampleRate_ = sampleRate;
        for (auto& line : lines_) line.assign(static_cast<size_t>(0.05 * sampleRate), 0.0f);
    }

    void process(mpc::ProcessContext& ctx) override {
        const float out = std::pow(10.0f, get(0) / 20.0f);
        const float inc = static_cast<float>(get(1) / sampleRate_);
        const float depth = static_cast<float>(get(2) * 0.001 * sampleRate_);
        const float wet = get(3) / 100.0f;
        for (int i = 0; i < ctx.numFrames; ++i) {
            for (int ch = 0; ch < 2; ++ch) {
                std::vector<float>& line = lines_[ch];
                const float x = ctx.inputs[ch][i];
                line[write_] = x;
                const float lfo = 0.5f + 0.5f * std::sin(6.2831853f * (phase_ + 0.25f * ch));
                const float delay = 1.0f + depth * lfo;
                const size_t n = line.size();
                const size_t read = (write_ + n - static_cast<size_t>(delay)) % n;
                ctx.outputs[ch][i] = out * (x + wet * (line[read] - x));
            }
            write_ = (write_ + 1) % lines_[0].size();
            phase_ += inc;
            if (phase_ >= 1.0f) phase_ -= 1.0f;
        }
    }

private:
    static mpc::PluginInfo makeInfo() {
        mpc::PluginInfo info;
        info.name = "Swirl";
        info.vendor = "Example Audio";
        info.uniqueId = MPC_FOURCC('E', 'x', 'S', 'w');
        info.isInstrument = false;
        info.numInputs = 2;
        info.numOutputs = 2;
        return info;
    }

    double sampleRate_ = 44100.0;
    std::vector<float> lines_[2];
    size_t write_ = 0;
    float phase_ = 0.0f;
};

MPC_PLUGIN_ENTRY(Swirl)
CPP
