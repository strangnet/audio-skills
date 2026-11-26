#pragma once

#include <juce_audio_processors/juce_audio_processors.h>

#include "../../core/tilt_eq.h"

// JUCE wrapper: adapts the portable core to VST3, AU and CLAP. It converts host
// buffers and parameters into plain types; the DSP stays in the core.
class TiltEqProcessor final : public juce::AudioProcessor {
public:
    TiltEqProcessor();

    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;
    void processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi) override;
    using AudioProcessor::processBlock;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int, const juce::String&) override {}

    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

private:
    juce::AudioProcessorValueTreeState state_;
    std::atomic<float>* output_ = nullptr;
    std::atomic<float>* tilt_ = nullptr;
    tilt::TiltEq eq_;
    juce::SmoothedValue<float, juce::ValueSmoothingTypes::Multiplicative> outputGain_{1.0f};

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(TiltEqProcessor)
};
