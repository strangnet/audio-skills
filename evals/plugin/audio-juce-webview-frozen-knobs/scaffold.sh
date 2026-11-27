#!/usr/bin/env bash
# A JUCE 9 WebView editor with three controls. Planted problems: the page requests the slider
# state "Drive" while the relay is named "drive", and it reads the bypass toggle relay with
# getSliderState. Mix is wired correctly. Registration, native integration and member order are
# right. No toolchains are needed.
set -euo pipefail
mkdir -p Source ui

cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.22)
project(Grit VERSION 1.0.0)
set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH "JUCE 9.0.x checkout")
add_subdirectory(${JUCE_DIR} juce)
juce_add_plugin(Grit COMPANY_NAME "Example" PLUGIN_MANUFACTURER_CODE Exmp PLUGIN_CODE Grit
    FORMATS VST3 AU PRODUCT_NAME "Grit")
target_sources(Grit PRIVATE Source/PluginProcessor.cpp Source/PluginEditor.cpp)
juce_add_binary_data(GritUi NAMESPACE GritUi HEADER_NAME GritUi.h SOURCES
    ui/index.html
    "${JUCE_DIR}/modules/juce_gui_extra/native/typescript/webview-interop/dist/index.js")
target_link_libraries(Grit PRIVATE GritUi juce::juce_audio_utils)
CMAKE

cat > Source/PluginEditor.h <<'CPP'
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

class GritProcessor;

class GritEditor final : public juce::AudioProcessorEditor {
public:
    explicit GritEditor(GritProcessor& p);
    void resized() override;

private:
    struct SinglePageBrowser final : juce::WebBrowserComponent {
        using WebBrowserComponent::WebBrowserComponent;
        bool pageAboutToLoad(const juce::String& url) override { return url == getResourceProviderRoot(); }
    };

    juce::WebSliderRelay driveRelay{"drive"};
    juce::WebSliderRelay mixRelay{"mix"};
    juce::WebToggleButtonRelay bypassRelay{"bypass"};

    SinglePageBrowser browser;

    juce::WebSliderParameterAttachment driveAttachment;
    juce::WebSliderParameterAttachment mixAttachment;
    juce::WebToggleButtonParameterAttachment bypassAttachment;
};
CPP

cat > Source/PluginEditor.cpp <<'CPP'
#include "PluginEditor.h"
#include "PluginProcessor.h"
#include <GritUi.h>

static std::optional<juce::WebBrowserComponent::Resource> getResource(const juce::String& url)
{
    auto bytes = [](const char* data, int size) {
        const auto* p = reinterpret_cast<const std::byte*>(data);
        return std::vector<std::byte>(p, p + size);
    };
    if (url == "/")
        return juce::WebBrowserComponent::Resource{bytes(GritUi::index_html, GritUi::index_htmlSize), "text/html"};
    if (url == "/juce/index.js")
        return juce::WebBrowserComponent::Resource{bytes(GritUi::index_js, GritUi::index_jsSize), "text/javascript"};
    return std::nullopt;
}

GritEditor::GritEditor(GritProcessor& p)
    : AudioProcessorEditor(&p),
      browser(juce::WebBrowserComponent::Options{}
                  .withNativeIntegrationEnabled()
                  .withOptionsFrom(driveRelay)
                  .withOptionsFrom(mixRelay)
                  .withOptionsFrom(bypassRelay)
                  .withResourceProvider(getResource)),
      driveAttachment(*p.state.getParameter("drive"), driveRelay),
      mixAttachment(*p.state.getParameter("mix"), mixRelay),
      bypassAttachment(*p.state.getParameter("bypass"), bypassRelay)
{
    addAndMakeVisible(browser);
    browser.goToURL(juce::WebBrowserComponent::getResourceProviderRoot());
    setSize(420, 220);
}

void GritEditor::resized() { browser.setBounds(getLocalBounds()); }
CPP

cat > Source/PluginProcessor.h <<'CPP'
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

// Processor (abridged): an APVTS named `state` holding float "drive" (0..36 dB),
// float "mix" (0..100 %) and bool "bypass", all created with ParameterID{id, 1}.
class GritProcessor final : public juce::AudioProcessor {
public:
    GritProcessor();
    juce::AudioProcessorValueTreeState state;
    // ... the usual AudioProcessor overrides ...
};
CPP

cat > Source/PluginProcessor.cpp <<'CPP'
#include "PluginProcessor.h"
#include "PluginEditor.h"
// Processor implementation omitted: createEditor() returns new GritEditor(*this).
CPP

cat > ui/index.html <<'HTML'
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Grit</title></head>
<body>
<label>Drive <input id="drive" type="range" min="0" max="1" step="any"></label>
<label>Mix <input id="mix" type="range" min="0" max="1" step="any"></label>
<button id="bypass">Bypass</button>
<script type="module">
  import * as Juce from "./juce/index.js";

  function bindSlider(element, state) {
    let editing = false;
    element.addEventListener("input", () => {
      if (!editing) { editing = true; state.sliderDragStarted(); }
      state.setNormalisedValue(Number(element.value));
    });
    element.addEventListener("change", () => { editing = false; state.sliderDragEnded(); });
    state.valueChangedEvent.addListener(() => {
      if (!editing) element.value = state.getNormalisedValue();
    });
  }

  bindSlider(document.getElementById("drive"), Juce.getSliderState("Drive"));
  bindSlider(document.getElementById("mix"), Juce.getSliderState("mix"));

  const bypass = Juce.getSliderState("bypass");
  const button = document.getElementById("bypass");
  button.addEventListener("click", () => {
    bypass.sliderDragStarted();
    bypass.setNormalisedValue(bypass.getNormalisedValue() < 0.5 ? 1 : 0);
    bypass.sliderDragEnded();
  });
</script>
</body>
</html>
HTML
