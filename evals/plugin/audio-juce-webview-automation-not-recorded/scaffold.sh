#!/usr/bin/env bash
# A JUCE 9 WebView editor whose page sets the cutoff slider's value on every input event but
# never calls sliderDragStarted() or sliderDragEnded(), so the host sees no gesture. The bypass
# toggle is correct (its attachment makes each change a complete gesture). No toolchains are
# needed.
set -euo pipefail
mkdir -p Source ui

cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.22)
project(Sweep VERSION 1.0.0)
set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH "JUCE 9.0.x checkout")
add_subdirectory(${JUCE_DIR} juce)
juce_add_plugin(Sweep COMPANY_NAME "Example" PLUGIN_MANUFACTURER_CODE Exmp PLUGIN_CODE Swep
    FORMATS VST3 AU PRODUCT_NAME "Sweep")
target_sources(Sweep PRIVATE Source/PluginProcessor.cpp Source/PluginEditor.cpp)
juce_add_binary_data(SweepUi NAMESPACE SweepUi HEADER_NAME SweepUi.h SOURCES
    ui/index.html
    "${JUCE_DIR}/modules/juce_gui_extra/native/typescript/webview-interop/dist/index.js")
target_link_libraries(Sweep PRIVATE SweepUi juce::juce_audio_utils)
CMAKE

cat > Source/PluginEditor.h <<'CPP'
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

class SweepProcessor;

class SweepEditor final : public juce::AudioProcessorEditor {
public:
    explicit SweepEditor(SweepProcessor& p);
    void resized() override;

private:
    struct SinglePageBrowser final : juce::WebBrowserComponent {
        using WebBrowserComponent::WebBrowserComponent;
        bool pageAboutToLoad(const juce::String& url) override { return url == getResourceProviderRoot(); }
    };

    juce::WebSliderRelay cutoffRelay{"cutoff"};
    juce::WebToggleButtonRelay bypassRelay{"bypass"};
    SinglePageBrowser browser;
    juce::WebSliderParameterAttachment cutoffAttachment;
    juce::WebToggleButtonParameterAttachment bypassAttachment;
};
CPP

cat > Source/PluginEditor.cpp <<'CPP'
#include "PluginEditor.h"
#include "PluginProcessor.h"
#include <SweepUi.h>

static std::optional<juce::WebBrowserComponent::Resource> getResource(const juce::String& url)
{
    auto bytes = [](const char* data, int size) {
        const auto* p = reinterpret_cast<const std::byte*>(data);
        return std::vector<std::byte>(p, p + size);
    };
    if (url == "/")
        return juce::WebBrowserComponent::Resource{bytes(SweepUi::index_html, SweepUi::index_htmlSize), "text/html"};
    if (url == "/juce/index.js")
        return juce::WebBrowserComponent::Resource{bytes(SweepUi::index_js, SweepUi::index_jsSize), "text/javascript"};
    return std::nullopt;
}

SweepEditor::SweepEditor(SweepProcessor& p)
    : AudioProcessorEditor(&p),
      browser(juce::WebBrowserComponent::Options{}
                  .withNativeIntegrationEnabled()
                  .withOptionsFrom(cutoffRelay)
                  .withOptionsFrom(bypassRelay)
                  .withResourceProvider(getResource)),
      cutoffAttachment(*p.state.getParameter("cutoff"), cutoffRelay),
      bypassAttachment(*p.state.getParameter("bypass"), bypassRelay)
{
    addAndMakeVisible(browser);
    browser.goToURL(juce::WebBrowserComponent::getResourceProviderRoot());
    setSize(400, 220);
}

void SweepEditor::resized() { browser.setBounds(getLocalBounds()); }
CPP

cat > Source/PluginProcessor.h <<'CPP'
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

// Processor (abridged): a low-pass filter with an APVTS named `state` holding float "cutoff"
// (20..20000 Hz, skewed) and bool "bypass", created with ParameterID{id, 1}.
class SweepProcessor final : public juce::AudioProcessor {
public:
    SweepProcessor();
    juce::AudioProcessorValueTreeState state;
    // ... the usual AudioProcessor overrides ...
};
CPP

cat > Source/PluginProcessor.cpp <<'CPP'
#include "PluginProcessor.h"
#include "PluginEditor.h"
// Processor implementation omitted: createEditor() returns new SweepEditor(*this).
CPP

cat > ui/index.html <<'HTML'
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Sweep</title></head>
<body>
<label>Cutoff <input id="cutoff" type="range" min="0" max="1" step="any"></label>
<button id="bypass">Bypass</button>
<script type="module">
  import * as Juce from "./juce/index.js";

  const knob = document.getElementById("cutoff");
  const cutoff = Juce.getSliderState("cutoff");
  knob.addEventListener("input", () => cutoff.setNormalisedValue(Number(knob.value)));
  cutoff.valueChangedEvent.addListener(() => { knob.value = cutoff.getNormalisedValue(); });

  const button = document.getElementById("bypass");
  const bypass = Juce.getToggleState("bypass");
  button.addEventListener("click", () => bypass.setValue(!bypass.getValue()));
  bypass.valueChangedEvent.addListener(() => button.classList.toggle("on", bypass.getValue()));
</script>
</body>
</html>
HTML
