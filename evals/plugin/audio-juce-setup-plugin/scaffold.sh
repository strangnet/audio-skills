#!/usr/bin/env bash
# A saturation effect's portable DSP core with a parameter table, and an empty juce/ folder.
# The prompt asks how to set up the JUCE 9 wrapper; no toolchains are needed.
set -euo pipefail
mkdir -p core juce/Source

cat > core/grit.h <<'CPP'
// Grit: header-only, standard-library-only saturation core.
#pragma once
#include <array>
#include <cmath>

namespace grit {

struct ParamInfo { const char* id; const char* name; float min, max, def; const char* unit; };

enum { kOutput, kDrive, kTone, kMix, kNumParams };

inline constexpr std::array<ParamInfo, kNumParams> kParams {{
    { "output", "Output", -24.0f, 24.0f, 0.0f, "dB" },
    { "drive",  "Drive",    0.0f, 36.0f, 12.0f, "dB" },
    { "tone",   "Tone",    -1.0f,  1.0f, 0.0f, "" },
    { "mix",    "Mix",      0.0f, 100.0f, 100.0f, "%" },
}};

class Grit {
public:
    void prepare(double sampleRate, int maxBlock) { sampleRate_ = sampleRate; (void)maxBlock; }
    void setParam(int index, float value) { values_[static_cast<size_t>(index)] = value; }
    // realtime
    void process(float* const* channels, int numChannels, int numFrames) {
        const float drive = std::pow(10.0f, values_[kDrive] / 20.0f);
        for (int ch = 0; ch < numChannels; ++ch)
            for (int i = 0; i < numFrames; ++i)
                channels[ch][i] = std::tanh(channels[ch][i] * drive);
    }
private:
    double sampleRate_ = 44100.0;
    std::array<float, kNumParams> values_ {};
};

}  // namespace grit
CPP
