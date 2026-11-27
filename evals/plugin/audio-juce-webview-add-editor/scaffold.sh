#!/usr/bin/env bash
# A JUCE 9 distortion effect with three parameters (float drive, bool bypass, choice mode)
# and no editor yet. The prompt asks how to add a WebView editor; no toolchains are needed.
set -euo pipefail
mkdir -p Source ui

cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.22)
project(Fuzzbox VERSION 1.0.0)
set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH "JUCE 9.0.x checkout")
add_subdirectory(${JUCE_DIR} juce)
juce_add_plugin(Fuzzbox
    COMPANY_NAME "Example"
    PLUGIN_MANUFACTURER_CODE Exmp
    PLUGIN_CODE Fuzz
    FORMATS VST3 AU
    PRODUCT_NAME "Fuzzbox")
target_sources(Fuzzbox PRIVATE Source/PluginProcessor.cpp)
target_compile_definitions(Fuzzbox PUBLIC JUCE_VST3_CAN_REPLACE_VST2=0)
target_link_libraries(Fuzzbox PRIVATE juce::juce_audio_utils)
CMAKE

cat > Source/PluginProcessor.h <<'CPP'
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

class FuzzboxProcessor final : public juce::AudioProcessor {
public:
    FuzzboxProcessor();
    void prepareToPlay(double, int) override {}
    void releaseResources() override {}
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override { return nullptr; }
    bool hasEditor() const override { return false; }
    const juce::String getName() const override { return "Fuzzbox"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int, const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override;
    void setStateInformation(const void*, int) override;

    juce::AudioProcessorValueTreeState state;

private:
    std::atomic<float>* drive_ = nullptr;
    std::atomic<float>* bypass_ = nullptr;
    std::atomic<float>* mode_ = nullptr;
};
CPP

cat > Source/PluginProcessor.cpp <<'CPP'
#include "PluginProcessor.h"

static juce::AudioProcessorValueTreeState::ParameterLayout makeLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID{"drive", 1}, "Drive", juce::NormalisableRange<float>(0.0f, 36.0f), 12.0f));
    layout.add(std::make_unique<juce::AudioParameterBool>(
        juce::ParameterID{"bypass", 1}, "Bypass", false));
    layout.add(std::make_unique<juce::AudioParameterChoice>(
        juce::ParameterID{"mode", 1}, "Mode", juce::StringArray{"Soft", "Hard", "Fold"}, 0));
    return layout;
}

FuzzboxProcessor::FuzzboxProcessor()
    : AudioProcessor(BusesProperties()
                         .withInput("Input", juce::AudioChannelSet::stereo(), true)
                         .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      state(*this, nullptr, "Fuzzbox", makeLayout())
{
    drive_ = state.getRawParameterValue("drive");
    bypass_ = state.getRawParameterValue("bypass");
    mode_ = state.getRawParameterValue("mode");
}

void FuzzboxProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;
    if (bypass_->load() >= 0.5f)
        return;
    const float gain = juce::Decibels::decibelsToGain(drive_->load());
    const int mode = static_cast<int>(mode_->load());
    for (int ch = 0; ch < buffer.getNumChannels(); ++ch) {
        auto* x = buffer.getWritePointer(ch);
        for (int i = 0; i < buffer.getNumSamples(); ++i) {
            const float in = x[i] * gain;
            x[i] = mode == 0 ? std::tanh(in) : mode == 1 ? juce::jlimit(-1.0f, 1.0f, in) : std::sin(in);
        }
    }
}

void FuzzboxProcessor::getStateInformation(juce::MemoryBlock& dest)
{
    if (auto xml = state.copyState().createXml())
        copyXmlToBinary(*xml, dest);
}

void FuzzboxProcessor::setStateInformation(const void* data, int size)
{
    if (auto xml = getXmlFromBinary(data, size))
        if (xml->hasTagName(state.state.getType()))
            state.replaceState(juce::ValueTree::fromXml(*xml));
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new FuzzboxProcessor(); }
CPP

cat > ui/README.txt <<'TXT'
The WebView page goes here.
TXT
