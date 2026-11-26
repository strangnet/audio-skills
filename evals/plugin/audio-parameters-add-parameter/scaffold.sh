#!/usr/bin/env bash
# A released tilt-EQ effect with a portable core, a JUCE wrapper and an MPC wrapper.
# Version 1.0.0 shipped with three parameters: out_gain (index 0), tilt, pivot.
# The prompt asks how to add a dry/wet mix parameter; no toolchains are needed.
set -euo pipefail
mkdir -p core juce mpc/src

cat > CHANGELOG.md <<'MD'
# Changelog

## 1.0.0 (released)

- First release: desktop (VST3, AU, CLAP) and MPC.
MD

cat > core/tilt_core.h <<'CPP'
// Portable tilt-EQ core: header-only C++17, standard library only.
#pragma once
#include <array>
#include <cmath>

namespace tilt {

enum Param { kOutGain = 0, kTilt, kPivot, kNumParams };

struct ParamInfo { const char* id; const char* name; float min, max, def; const char* unit; };

inline constexpr std::array<ParamInfo, kNumParams> kParams {{
    { "out_gain", "Output", -12.0f, 12.0f,   0.0f,   "dB" },
    { "tilt",     "Tilt",    -6.0f,  6.0f,   0.0f,   "dB" },
    { "pivot",    "Pivot",  200.0f, 5000.0f, 1000.0f, "Hz" },
}};

class Core {
public:
    void prepare(double sampleRate) { sampleRate_ = sampleRate; }
    void setParam(int index, float plain) { values_[index] = plain; }
    // realtime
    void process(float* const* channels, int numChannels, int numFrames) noexcept
    {
        const float gain = std::pow(10.0f, values_[kOutGain] / 20.0f);
        for (int c = 0; c < numChannels; ++c)
            for (int i = 0; i < numFrames; ++i)
                channels[c][i] *= gain; // tilt filter omitted in this sketch
    }
private:
    double sampleRate_ = 44100.0;
    std::array<float, kNumParams> values_ { 0.0f, 0.0f, 1000.0f };
};

} // namespace tilt
CPP

cat > juce/PluginProcessor.cpp <<'CPP'
// JUCE wrapper (sketch): parameters come from tilt::kParams.
#include "PluginProcessor.h"

juce::AudioProcessorValueTreeState::ParameterLayout TiltProcessor::createLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    for (const auto& p : tilt::kParams)
        layout.add(std::make_unique<juce::AudioParameterFloat>(
            juce::ParameterID { p.id, 1 }, p.name,
            juce::NormalisableRange<float> { p.min, p.max }, p.def));
    return layout;
}

void TiltProcessor::getStateInformation(juce::MemoryBlock& dest)
{
    if (auto xml = apvts.copyState().createXml())
        copyXmlToBinary(*xml, dest);
}

void TiltProcessor::setStateInformation(const void* data, int size)
{
    if (auto xml = getXmlFromBinary(data, size))
        apvts.replaceState(juce::ValueTree::fromXml(*xml));
}
CPP

cat > mpc/plugin.json <<'JSON'
{
  "name": "Tilt EQ",
  "manufacturer": "Example",
  "kind": "effect",
  "shortName": "Tilt EQ",
  "knobs": [
    { "parameter": 1, "label": "Tilt" },
    { "parameter": 2, "label": "Pivot" }
  ]
}
JSON

cat > mpc/src/TiltEq.cpp <<'CPP'
// MPC wrapper (sketch): an mpc::Plugin subclass around tilt::Core.
#include "mpc_plugin.h"
#include "../../core/tilt_core.h"

class TiltEq : public mpc::Plugin {
public:
    TiltEq() : mpc::Plugin(info())
    {
        addParam(mpc::floatParam("out_gain", "Output", -12, 12, 0, "dB", 1));
        addParam(mpc::floatParam("tilt", "Tilt", -6, 6, 0, "dB", 1));
        addParam(mpc::logParam("pivot", "Pivot", 200, 5000, 1000, "Hz", 0));
        addProgram("Init", { 0.0f, 0.0f, 1000.0f });
        addProgram("Bright", { 0.0f, 3.0f, 800.0f });
    }
    void process(mpc::ProcessContext& ctx) override { (void)ctx; }
};

MPC_PLUGIN_ENTRY(TiltEq)
CPP
