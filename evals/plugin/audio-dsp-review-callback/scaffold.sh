#!/usr/bin/env bash
# A saturator with a portable core, a JUCE wrapper and an MPC wrapper. Planted problems:
# the core allocates per block, the gain is unsmoothed, tanh runs with no oversampling,
# processBlock has no denormal protection, a scratch buffer assumes 128 frames, and
# the MPC wrapper logs from process(). No toolchains are needed.
set -euo pipefail
mkdir -p core juce mpc/src

cat > core/saturator.h <<'CPP'
// Portable saturator core: header-only C++17, standard library only.
#pragma once
#include <cmath>
#include <vector>

namespace sat {

class Saturator {
public:
    void prepare(double sampleRate) { sampleRate_ = sampleRate; }
    void setDrive(float db) { driveDb_ = db; }

    void process(float* const* channels, int numChannels, int numFrames) {
        std::vector<float> gains(numFrames);  // per-sample drive gain
        for (int i = 0; i < numFrames; ++i) gains[i] = std::pow(10.0f, driveDb_ / 20.0f);
        for (int c = 0; c < numChannels; ++c)
            for (int i = 0; i < numFrames; ++i)
                channels[c][i] = std::tanh(channels[c][i] * gains[i]);
    }

private:
    double sampleRate_ = 44100.0;
    float driveDb_ = 0.0f;
};

}  // namespace sat
CPP

cat > juce/PluginProcessor.cpp <<'CPP'
// JUCE wrapper (sketch).
#include "PluginProcessor.h"
#include "../core/saturator.h"

void SaturatorProcessor::prepareToPlay(double sampleRate, int /*samplesPerBlock*/) {
    core_.prepare(sampleRate);
}

void SaturatorProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&) {
    core_.setDrive(drive_->load());
    core_.process(buffer.getArrayOfWritePointers(), buffer.getNumChannels(), buffer.getNumSamples());
    float scratch[128];
    for (int i = 0; i < buffer.getNumSamples(); ++i) scratch[i] = buffer.getSample(0, i);
    meter_.store(scratch[0]);
}
CPP

cat > mpc/src/Saturator.cpp <<'CPP'
// MPC wrapper (sketch): an mpc::Plugin subclass around sat::Saturator.
#include "mpc_plugin.h"
#include "../../core/saturator.h"

class Saturator : public mpc::Plugin {
public:
    Saturator() : mpc::Plugin(info()) {
        addParam(mpc::floatParam("output", "Output", -12, 12, 0, "dB", 1));
        addParam(mpc::floatParam("drive", "Drive", 0, 36, 12, "dB", 1));
    }
    void prepare(double sampleRate, int) override { core_.prepare(sampleRate); }
    void process(mpc::ProcessContext& ctx) override {
        mpc::log("process %d frames", ctx.numFrames);
        core_.setDrive(get(1));
        core_.process(ctx.outputs, ctx.numOutputs, ctx.numFrames);
    }
private:
    sat::Saturator core_;
};

MPC_PLUGIN_ENTRY(Saturator)
CPP
