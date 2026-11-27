#!/usr/bin/env bash
# Routing to audio-dsp: an MPC echo effect kept in my-plugin/, outside any SDK checkout, whose
# process() callback has planted real-time problems: a scratch buffer sized for 128 frames, an
# allocation and a log line per block, and std::pow per sample. The prompt is about the audio
# callback, so the advice belongs to audio-dsp; audio-mpc may fire too but only names it.
# No SDK or toolchain is needed.
set -euo pipefail
mkdir -p my-plugin/src

cat > my-plugin/plugin.json <<'JSON'
{
  "name": "Echo",
  "manufacturer": "Example Audio",
  "version": "1.0.0",
  "format": "vst2",
  "kind": "effect",
  "uid": "ExEc",
  "numInputs": 2,
  "numOutputs": 2,
  "shortName": "Echo",
  "knobs": [
    { "parameter": 1, "label": "Time" },
    { "parameter": 2, "label": "Feedback" },
    { "parameter": 3, "label": "Mix" }
  ],
  "shiftKnobs": [
    { "parameter": 0, "label": "Output" }
  ],
  "file32": "VST/echo-arm32.so",
  "file64": "VST/echo-arm64.so"
}
JSON

cat > my-plugin/src/Echo.cpp <<'CPP'
// Echo: a feedback delay for the MPC. Signal flow: input -> delay line with feedback ->
// dry/wet mix -> output trim. Parameter 0 is the output trim.
#include "mpc_plugin.h"

#include <cmath>
#include <cstdio>
#include <vector>

class Echo : public mpc::Plugin {
public:
    Echo() : mpc::Plugin(makeInfo()) {
        addParam(mpc::floatParam("output", "Output", -24, 6, 0, "dB", 1));
        addParam(mpc::floatParam("time", "Time", 10, 1000, 350, "ms", 0));
        addParam(mpc::floatParam("feedback", "Feedback", 0, 95, 40, "%", 0));
        addParam(mpc::floatParam("mix", "Mix", 0, 100, 35, "%", 0));
    }

    void prepare(double sampleRate, int maxBlockSize) override {
        sampleRate_ = sampleRate;
        line_[0].assign(static_cast<size_t>(sampleRate), 0.0f);
        line_[1].assign(static_cast<size_t>(sampleRate), 0.0f);
        (void)maxBlockSize;
    }

    void process(mpc::ProcessContext& ctx) override {
        float wetBlock[2][128];                       // one MPC block
        std::vector<float> gains(ctx.numFrames);      // per-sample output gain
        std::printf("Echo: block of %d frames\n", ctx.numFrames);

        const int delay = static_cast<int>(get(1) * 0.001 * sampleRate_);
        const float fb = get(2) / 100.0f;
        const float wet = get(3) / 100.0f;
        for (int i = 0; i < 128; ++i) gains[i] = std::pow(10.0f, get(0) / 20.0f);

        for (int ch = 0; ch < 2; ++ch) {
            std::vector<float>& line = line_[ch];
            for (int i = 0; i < 128; ++i) {
                const size_t read = (write_ + line.size() - delay + i) % line.size();
                wetBlock[ch][i] = line[read];
                line[(write_ + i) % line.size()] = ctx.inputs[ch][i] + fb * line[read];
            }
            for (int i = 0; i < 128; ++i) {
                ctx.outputs[ch][i] = gains[i] * (ctx.inputs[ch][i] + wet * (wetBlock[ch][i] - ctx.inputs[ch][i]));
            }
        }
        write_ = (write_ + 128) % line_[0].size();
    }

private:
    static mpc::PluginInfo makeInfo() {
        mpc::PluginInfo info;
        info.name = "Echo";
        info.vendor = "Example Audio";
        info.uniqueId = MPC_FOURCC('E', 'x', 'E', 'c');
        info.isInstrument = false;
        info.numInputs = 2;
        info.numOutputs = 2;
        return info;
    }

    double sampleRate_ = 44100.0;
    std::vector<float> line_[2];
    size_t write_ = 0;
};

MPC_PLUGIN_ENTRY(Echo)
CPP
