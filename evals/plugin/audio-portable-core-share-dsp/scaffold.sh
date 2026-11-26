#!/usr/bin/env bash
# A JUCE compressor whose DSP lives inside processBlock and uses JUCE types throughout.
# The prompt asks how to share its DSP with a new MPC plugin; no toolchains are needed.
set -euo pipefail
mkdir -p juce/Source

cat > juce/CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.22)
project(Squash VERSION 1.0.0)
add_subdirectory(${JUCE_DIR} juce)
juce_add_plugin(Squash COMPANY_NAME "Example" PLUGIN_MANUFACTURER_CODE Exmp PLUGIN_CODE Sqsh
    FORMATS VST3 AU PRODUCT_NAME "Squash")
target_sources(Squash PRIVATE Source/PluginProcessor.cpp)
target_link_libraries(Squash PRIVATE juce::juce_audio_utils juce::juce_dsp)
CMAKE

cat > juce/Source/PluginProcessor.cpp <<'CPP'
// JUCE compressor: the DSP is written directly against JUCE types.
#include "PluginProcessor.h"

juce::AudioProcessorValueTreeState::ParameterLayout SquashProcessor::createLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    layout.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID { "threshold", 1 }, "Threshold",
        juce::NormalisableRange<float> { -60.0f, 0.0f }, -18.0f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID { "ratio", 1 }, "Ratio",
        juce::NormalisableRange<float> { 1.0f, 20.0f, 0.0f, 0.4f }, 4.0f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID { "attack", 1 }, "Attack",
        juce::NormalisableRange<float> { 0.1f, 100.0f, 0.0f, 0.3f }, 10.0f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID { "release", 1 }, "Release",
        juce::NormalisableRange<float> { 10.0f, 1000.0f, 0.0f, 0.3f }, 120.0f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID { "makeup", 1 }, "Makeup",
        juce::NormalisableRange<float> { 0.0f, 24.0f }, 0.0f));
    return layout;
}

void SquashProcessor::prepareToPlay(double sampleRate, int samplesPerBlock)
{
    juce::dsp::ProcessSpec spec { sampleRate, (juce::uint32) samplesPerBlock, 2 };
    envelope_.prepare(spec);
    makeup_.prepare(spec);
    makeup_.setRampDurationSeconds(0.02);
}

void SquashProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;
    const float threshold = apvts.getRawParameterValue("threshold")->load();
    const float ratio = apvts.getRawParameterValue("ratio")->load();
    envelope_.setAttackTime(apvts.getRawParameterValue("attack")->load());
    envelope_.setReleaseTime(apvts.getRawParameterValue("release")->load());
    makeup_.setGainDecibels(apvts.getRawParameterValue("makeup")->load());

    for (int i = 0; i < buffer.getNumSamples(); ++i)
    {
        const float peak = juce::jmax(std::abs(buffer.getSample(0, i)), std::abs(buffer.getSample(1, i)));
        const float level = juce::Decibels::gainToDecibels(envelope_.processSample(0, peak));
        const float over = juce::jmax(0.0f, level - threshold);
        const float gain = juce::Decibels::decibelsToGain(-over * (1.0f - 1.0f / ratio));
        for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
            buffer.setSample(ch, i, buffer.getSample(ch, i) * gain);
    }
    juce::dsp::AudioBlock<float> block(buffer);
    makeup_.process(juce::dsp::ProcessContextReplacing<float>(block));
}
CPP
