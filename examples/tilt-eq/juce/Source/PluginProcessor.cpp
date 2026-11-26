#include "PluginProcessor.h"

#include "PluginEditor.h"

namespace {

// The parameters come from the core's table (tilt::kParams): the same ids and the
// same order as the MPC wrapper. Ids are stable forever.
juce::AudioProcessorValueTreeState::ParameterLayout createLayout() {
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    for (const auto& p : tilt::kParams) {
        layout.add(std::make_unique<juce::AudioParameterFloat>(
            juce::ParameterID{p.id, 1}, p.name, juce::NormalisableRange<float>(p.min, p.max, 0.01f), p.def,
            juce::AudioParameterFloatAttributes().withLabel(p.unit)));
    }
    return layout;
}

}  // namespace

TiltEqProcessor::TiltEqProcessor()
    : AudioProcessor(BusesProperties()
                         .withInput("Input", juce::AudioChannelSet::stereo(), true)
                         .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      state_(*this, nullptr, "TiltEqState", createLayout()) {
    for (int i = 0; i < tilt::kNumParams; ++i)
        params_[static_cast<size_t>(i)] = state_.getRawParameterValue(tilt::kParams[static_cast<size_t>(i)].id);
}

void TiltEqProcessor::prepareToPlay(double sampleRate, int /*samplesPerBlock*/) {
    eq_.prepare(sampleRate);
    pushParams();
}

void TiltEqProcessor::pushParams() {
    for (int i = 0; i < tilt::kNumParams; ++i)
        eq_.setParam(i, params_[static_cast<size_t>(i)]->load());
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
    pushParams();
    eq_.process(buffer.getArrayOfWritePointers(), buffer.getNumChannels(), buffer.getNumSamples());
}

juce::AudioProcessorEditor* TiltEqProcessor::createEditor() {
    return new TiltEqEditor(*this, *state_.getParameter(tilt::kParams[tilt::kTilt].id));
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
