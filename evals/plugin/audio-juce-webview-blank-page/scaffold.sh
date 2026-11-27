#!/usr/bin/env bash
# A JUCE 9 WebView editor that goes to the resource provider's root, but its provider strips the
# leading slash and only knows "index.html" and "js/juce/index.js", so the root request ("/")
# finds nothing and the page stays blank. Everything else is wired correctly. No toolchains are
# needed.
set -euo pipefail
mkdir -p Source ui

cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.22)
project(Hush VERSION 1.0.0)
set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH "JUCE 9.0.x checkout")
add_subdirectory(${JUCE_DIR} juce)
juce_add_plugin(Hush COMPANY_NAME "Example" PLUGIN_MANUFACTURER_CODE Exmp PLUGIN_CODE Hush
    FORMATS VST3 AU PRODUCT_NAME "Hush")
target_sources(Hush PRIVATE Source/PluginProcessor.cpp Source/PluginEditor.cpp)
juce_add_binary_data(HushUi NAMESPACE HushUi HEADER_NAME HushUi.h SOURCES
    ui/index.html
    "${JUCE_DIR}/modules/juce_gui_extra/native/typescript/webview-interop/dist/index.js")
target_link_libraries(Hush PRIVATE HushUi juce::juce_audio_utils)
CMAKE

cat > Source/PluginEditor.h <<'CPP'
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

class HushProcessor;

class HushEditor final : public juce::AudioProcessorEditor {
public:
    explicit HushEditor(HushProcessor& p);
    void resized() override;

private:
    juce::WebSliderRelay thresholdRelay{"threshold"};
    juce::WebBrowserComponent browser;
    juce::WebSliderParameterAttachment thresholdAttachment;
};
CPP

cat > Source/PluginEditor.cpp <<'CPP'
#include "PluginEditor.h"
#include "PluginProcessor.h"
#include <HushUi.h>

static std::optional<juce::WebBrowserComponent::Resource> getResource(const juce::String& url)
{
    auto bytes = [](const char* data, int size) {
        const auto* p = reinterpret_cast<const std::byte*>(data);
        return std::vector<std::byte>(p, p + size);
    };
    const auto path = url.substring(1);  // drop the leading slash
    if (path == "index.html")
        return juce::WebBrowserComponent::Resource{bytes(HushUi::index_html, HushUi::index_htmlSize), "text/html"};
    if (path == "js/juce/index.js")
        return juce::WebBrowserComponent::Resource{bytes(HushUi::index_js, HushUi::index_jsSize), "text/javascript"};
    return std::nullopt;
}

HushEditor::HushEditor(HushProcessor& p)
    : AudioProcessorEditor(&p),
      browser(juce::WebBrowserComponent::Options{}
                  .withNativeIntegrationEnabled()
                  .withOptionsFrom(thresholdRelay)
                  .withResourceProvider(getResource)),
      thresholdAttachment(*p.state.getParameter("threshold"), thresholdRelay)
{
    addAndMakeVisible(browser);
    browser.goToURL(juce::WebBrowserComponent::getResourceProviderRoot());
    setSize(400, 200);
}

void HushEditor::resized() { browser.setBounds(getLocalBounds()); }
CPP

cat > Source/PluginProcessor.h <<'CPP'
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

// Processor (abridged): a noise gate with an APVTS named `state` holding float "threshold"
// (-80..0 dB), created with ParameterID{"threshold", 1}.
class HushProcessor final : public juce::AudioProcessor {
public:
    HushProcessor();
    juce::AudioProcessorValueTreeState state;
    // ... the usual AudioProcessor overrides ...
};
CPP

cat > Source/PluginProcessor.cpp <<'CPP'
#include "PluginProcessor.h"
#include "PluginEditor.h"
// Processor implementation omitted: createEditor() returns new HushEditor(*this).
CPP

cat > ui/index.html <<'HTML'
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Hush</title></head>
<body>
<label>Threshold <input id="threshold" type="range" min="0" max="1" step="any"></label>
<script type="module">
  import * as Juce from "./js/juce/index.js";

  const input = document.getElementById("threshold");
  const threshold = Juce.getSliderState("threshold");
  let editing = false;
  input.addEventListener("input", () => {
    if (!editing) { editing = true; threshold.sliderDragStarted(); }
    threshold.setNormalisedValue(Number(input.value));
  });
  input.addEventListener("change", () => { editing = false; threshold.sliderDragEnded(); });
  threshold.valueChangedEvent.addListener(() => {
    if (!editing) input.value = threshold.getNormalisedValue();
  });
</script>
</body>
</html>
HTML
