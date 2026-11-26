#!/usr/bin/env bash
# A saturation effect released as 1.2.0 on desktop and MPC, with parameters
# out_gain (0), drive (1), tone (2, no longer used by the DSP) and mix (3).
# The prompt asks to rename Drive and remove Tone.
set -euo pipefail
mkdir -p core juce mpc/src

cat > CHANGELOG.md <<'MD'
# Changelog

## 1.2.0 (released)

- Tone no longer affects the sound (the new saturation curve made it redundant).

## 1.1.0 (released)

- Added Mix.

## 1.0.0 (released)

- First release: desktop (VST3, AU, CLAP) and MPC.
MD

cat > core/crunch_core.h <<'CPP'
// Portable saturation core: header-only C++17, standard library only.
#pragma once
#include <array>

namespace crunch {

enum Param { kOutGain = 0, kDrive, kTone, kMix, kNumParams };

struct ParamInfo { const char* id; const char* name; float min, max, def; const char* unit; };

inline constexpr std::array<ParamInfo, kNumParams> kParams {{
    { "out_gain", "Output", -12.0f, 12.0f, 0.0f,   "dB" },
    { "drive",    "Drive",    0.0f, 24.0f, 6.0f,   "dB" },
    { "tone",     "Tone",     0.0f,  1.0f, 0.5f,   ""   }, // unused since 1.2.0
    { "mix",      "Mix",      0.0f, 100.0f, 100.0f, "%" },
}};

} // namespace crunch
CPP

cat > juce/PluginProcessor.cpp <<'CPP'
// JUCE wrapper (sketch): parameters come from crunch::kParams.
#include "PluginProcessor.h"

juce::AudioProcessorValueTreeState::ParameterLayout CrunchProcessor::createLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    for (const auto& p : crunch::kParams)
        layout.add(std::make_unique<juce::AudioParameterFloat>(
            juce::ParameterID { p.id, 1 }, p.name,
            juce::NormalisableRange<float> { p.min, p.max }, p.def));
    return layout;
}

void CrunchProcessor::setStateInformation(const void* data, int size)
{
    if (auto xml = getXmlFromBinary(data, size))
        apvts.replaceState(juce::ValueTree::fromXml(*xml));
}
CPP

cat > mpc/plugin.json <<'JSON'
{
  "name": "Crunch",
  "manufacturer": "Example",
  "kind": "effect",
  "shortName": "Crunch",
  "knobs": [
    { "parameter": 1, "label": "Drive" },
    { "parameter": 3, "label": "Mix" },
    { "parameter": 0, "label": "Output" }
  ]
}
JSON

cat > mpc/src/Crunch.cpp <<'CPP'
// MPC wrapper (sketch): an mpc::Plugin subclass around crunch's core.
#include "mpc_plugin.h"
#include "../../core/crunch_core.h"

class Crunch : public mpc::Plugin {
public:
    Crunch() : mpc::Plugin(info())
    {
        addParam(mpc::floatParam("out_gain", "Output", -12, 12, 0, "dB", 1));
        addParam(mpc::floatParam("drive", "Drive", 0, 24, 6, "dB", 1));
        addParam(mpc::floatParam("tone", "Tone", 0, 1, 0.5f));
        addParam(mpc::floatParam("mix", "Mix", 0, 100, 100, "%", 0));
        addProgram("Init", { 0.0f, 6.0f, 0.5f, 100.0f });
        addProgram("Fuzz", { -6.0f, 20.0f, 0.5f, 80.0f });
    }
    void process(mpc::ProcessContext& ctx) override { (void)ctx; }
};

MPC_PLUGIN_ENTRY(Crunch)
CPP
