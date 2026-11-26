#include "PluginEditor.h"

#include <TiltEqUi.h>

namespace {

using Resource = juce::WebBrowserComponent::Resource;

// The UI files, embedded with juce_add_binary_data. "juce/index.js" is JUCE's own
// webview-interop library, taken from the JUCE checkout so its version always
// matches the C++ side.
std::optional<Resource> getResource(const juce::String& url) {
    struct Entry {
        const char* path;
        const char* data;
        int size;
        const char* mimeType;
    };
    static const Entry files[] = {
        {"index.html", TiltEqUi::index_html, TiltEqUi::index_htmlSize, "text/html"},
        {"juce/index.js", TiltEqUi::index_js, TiltEqUi::index_jsSize, "text/javascript"},
    };

    // The provider receives "/" for the root and "/path" for everything else.
    const auto path = url == "/" ? juce::String("index.html")
                                 : url.fromFirstOccurrenceOf("/", false, false);
    for (const auto& file : files) {
        if (path == file.path) {
            const auto* bytes = reinterpret_cast<const std::byte*>(file.data);
            return Resource{std::vector<std::byte>(bytes, bytes + file.size), file.mimeType};
        }
    }
    return std::nullopt;
}

}  // namespace

bool TiltEqEditor::SinglePageBrowser::pageAboutToLoad(const juce::String& newURL) {
    return newURL == getResourceProviderRoot();
}

TiltEqEditor::TiltEqEditor(juce::AudioProcessor& owner, juce::RangedAudioParameter& tilt)
    : AudioProcessorEditor(&owner),
      browser_(juce::WebBrowserComponent::Options{}
                   .withNativeIntegrationEnabled()
                   .withOptionsFrom(tiltRelay_)
                   .withResourceProvider(getResource)),
      tiltAttachment_(tilt, tiltRelay_) {
    addAndMakeVisible(browser_);
    browser_.goToURL(juce::WebBrowserComponent::getResourceProviderRoot());
    setSize(360, 160);
}

void TiltEqEditor::resized() {
    browser_.setBounds(getLocalBounds());
}
