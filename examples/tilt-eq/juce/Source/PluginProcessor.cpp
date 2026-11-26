#include "PluginProcessor.h"

namespace {

// Stable parameter id: never rename or reuse it once released.
const juce::ParameterID kTiltId{"tilt", 1};

juce::AudioProcessorValueTreeState::ParameterLayout createLayout() {
    return {std::make_unique<juce::AudioParameterFloat>(
        kTiltId, "Tilt", juce::NormalisableRange<float>(-12.0f, 12.0f, 0.01f), 0.0f,
        juce::AudioParameterFloatAttributes().withLabel("dB"))};
}

}  // namespace

TiltEqProcessor::TiltEqProcessor()
    : AudioProcessor(BusesProperties()
                         .withInput("Input", juce::AudioChannelSet::stereo(), true)
                         .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      state_(*this, nullptr, "TiltEqState", createLayout()),
      tilt_(state_.getRawParameterValue(kTiltId.getParamID())) {}

void TiltEqProcessor::prepareToPlay(double sampleRate, int /*samplesPerBlock*/) {
    eq_.prepare(sampleRate);
    eq_.setTilt(tilt_->load());
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
}

juce::AudioProcessorEditor* TiltEqProcessor::createEditor() {
    return new juce::GenericAudioProcessorEditor(*this);
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
