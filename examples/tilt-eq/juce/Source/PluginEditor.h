#pragma once

#include <juce_audio_processors/juce_audio_processors.h>

// WebView editor: one tilt slider in ui/index.html, bound to the tilt parameter
// through JUCE's WebSliderRelay and WebSliderParameterAttachment, so drags reach
// the host as gestures and host automation moves the slider.
class TiltEqEditor final : public juce::AudioProcessorEditor {
public:
    TiltEqEditor(juce::AudioProcessor& owner,juce::RangedAudioParameter& tilt);

    void resized() override;

private:
    // Keeps the WebView on the plugin's own page: no navigation elsewhere.
    struct SinglePageBrowser final : juce::WebBrowserComponent {
        using WebBrowserComponent::WebBrowserComponent;
        bool pageAboutToLoad(const juce::String& newURL) override;
    };

    // Order matters: the relay must outlive the browser that holds its options,
    // and the attachment must be created after both and destroyed before them.
    juce::WebSliderRelay tiltRelay_{"tilt"};
    SinglePageBrowser browser_;
    juce::WebSliderParameterAttachment tiltAttachment_;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(TiltEqEditor)
};
