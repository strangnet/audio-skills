#include "PluginProcessor.h"

#include "PluginEditor.h"

namespace {

// Stable parameter ids: never rename or reuse them once released.
const juce::ParameterID kOutputId{"output", 1};
const juce::ParameterID kTiltId{"tilt", 1};

constexpr double kOutputSmoothingSeconds = 0.020;

// The order matches the MPC wrapper: Output (index 0, harmless at its 0 dB
// default, because the MPC nudges parameter 0), then Tilt.
juce::AudioProcessorValueTreeState::ParameterLayout createLayout() {
    const auto dB = juce::AudioParameterFloatAttributes().withLabel("dB");
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        kOutputId, "Output", juce::NormalisableRange<float>(-12.0f, 12.0f, 0.01f), 0.0f, dB));
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        kTiltId, "Tilt", juce::NormalisableRange<float>(-12.0f, 12.0f, 0.01f), 0.0f, dB));
    return layout;
}

}  // namespace

TiltEqProcessor::TiltEqProcessor()
    : AudioProcessor(BusesProperties()
                         .withInput("Input", juce::AudioChannelSet::stereo(), true)
                         .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      state_(*this, nullptr, "TiltEqState", createLayout()),
      output_(state_.getRawParameterValue(kOutputId.getParamID())),
      tilt_(state_.getRawParameterValue(kTiltId.getParamID())) {}

void TiltEqProcessor::prepareToPlay(double sampleRate, int /*samplesPerBlock*/) {
    eq_.prepare(sampleRate);
    eq_.setTilt(tilt_->load());
    outputGain_.reset(sampleRate, kOutputSmoothingSeconds);
    outputGain_.setCurrentAndTargetValue(juce::Decibels::decibelsToGain(output_->load()));
}

bool TiltEqProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const {
    // The core holds filter state for at most two channels.
    const auto out = layouts.getMainOutputChannelSet();
    if (out != juce::AudioChannelSet::mono() && out != juce::AudioChannelSet::stereo())
        return false;
    return out == layouts.getMainInputChannelSet();
}

void TiltEqProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& /*midi*/) {
    juce::ScopedNoDenormals noDenormals;
    eq_.setTilt(tilt_->load());
    eq_.process(buffer.getArrayOfWritePointers(), buffer.getNumChannels(), buffer.getNumSamples());
    outputGain_.setTargetValue(juce::Decibels::decibelsToGain(output_->load()));
    outputGain_.applyGain(buffer, buffer.getNumSamples());
}

juce::AudioProcessorEditor* TiltEqProcessor::createEditor() {
    return new TiltEqEditor(*this, *state_.getParameter(kTiltId.getParamID()));
}

void TiltEqProcessor::getStateInformation(juce::MemoryBlock& destData) {
    if (auto xml = state_.copyState().createXml())
        copyXmlToBinary(*xml, destData);
}

void TiltEqProcessor::setStateInformation(const void* data, int sizeInBytes) {
    if (auto xml = getXmlFromBinary(data, sizeInBytes))
        if (xml->hasTagName(state_.state.getType()))
            state_.replaceState(juce::ValueTree::fromXml(*xml));
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() {
    return new TiltEqProcessor();
}
