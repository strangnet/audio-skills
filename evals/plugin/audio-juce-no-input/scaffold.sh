#!/usr/bin/env bash
# A JUCE 9 delay effect whose processor uses the default AudioProcessor constructor, so its
# buses exist but are disabled by default. The host gives it no input. No toolchains are needed.
set -euo pipefail
mkdir -p Source

cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.22)
project(Echoes VERSION 1.0.0)
set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH "JUCE checkout")
add_subdirectory(${JUCE_DIR} juce)
juce_add_plugin(Echoes COMPANY_NAME "Example" PLUGIN_MANUFACTURER_CODE Exmp PLUGIN_CODE Echo
    FORMATS VST3 AU PRODUCT_NAME "Echoes")
target_sources(Echoes PRIVATE Source/PluginProcessor.cpp)
target_link_libraries(Echoes PRIVATE juce::juce_audio_utils)
CMAKE

cat > Source/PluginProcessor.h <<'CPP'
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

class EchoesProcessor final : public juce::AudioProcessor {
public:
    EchoesProcessor();
    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override { return nullptr; }
    bool hasEditor() const override { return false; }
    const juce::String getName() const override { return "Echoes"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 2.0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int, const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override {}
    void setStateInformation(const void*, int) override {}
private:
    juce::AudioBuffer<float> delay_;
    int writePos_ = 0;
};
CPP

cat > Source/PluginProcessor.cpp <<'CPP'
#include "PluginProcessor.h"

EchoesProcessor::EchoesProcessor() {}

void EchoesProcessor::prepareToPlay(double sampleRate, int)
{
    delay_.setSize(2, static_cast<int>(sampleRate * 2.0));
    delay_.clear();
    writePos_ = 0;
}

void EchoesProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;
    const int len = delay_.getNumSamples();
    for (int i = 0; i < buffer.getNumSamples(); ++i)
    {
        for (int ch = 0; ch < juce::jmin(2, buffer.getNumChannels()); ++ch)
        {
            const float in = buffer.getSample(ch, i);
            const float out = in + 0.5f * delay_.getSample(ch, writePos_);
            delay_.setSample(ch, writePos_, in + 0.4f * delay_.getSample(ch, writePos_));
            buffer.setSample(ch, i, out);
        }
        writePos_ = (writePos_ + 1) % len;
    }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new EchoesProcessor(); }
CPP
