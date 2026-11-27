---
name: audio-juce
description: JUCE 9 know-how for desktop audio plugins built with CMake on macOS (VST3 and AU from JUCE, CLAP through clap-juce-extensions), covering finding JUCE, plugin and manufacturer codes, module headers, bus layouts for effects and instruments, the parameter tree, which thread does what, the editor's lifecycle, programs and state, and host-facing pitfalls. Use when setting up, configuring or fixing a JUCE plugin project (`juce_add_plugin`, its `CMakeLists.txt`, formats, the `AudioProcessor`); when adding CLAP to a JUCE plugin; when writing a JUCE instrument; or when an effect gets no input, an instrument is listed as an effect or gets no MIDI, or a plugin appears twice in a host. Not for WebView editor details (use `audio-juce-webview`) or Component-based editors. Not for work inside an Akai MPC SDK checkout, which Akai's own `mpc-plugin-*` skills cover (use those there). Not for other plugin frameworks such as iPlug2 or nih-plug, and not for Claude Code or Cowork plugins.
---

# Audio JUCE

JUCE 9 builds a plugin from one `AudioProcessor` and one CMake call. Most JUCE mistakes compile cleanly and only show up in a host: a plugin code that changes on every configure, an effect with no input, an instrument the host files under effects. Everything here is checked against JUCE 9.0.6 on macOS; each reference names the JUCE file it comes from. Windows isn't covered.

## Rules

- **Find JUCE through a CMake cache variable or an environment variable**, such as `set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH ...)` and `add_subdirectory(${JUCE_DIR} juce)`, or `find_package(JUCE CONFIG)` with `CMAKE_PREFIX_PATH`. Never write an absolute path into `CMakeLists.txt`.
- **Set a fixed, unique four-character `PLUGIN_CODE` and `PLUGIN_MANUFACTURER_CODE`.** Leave out `PLUGIN_CODE` and JUCE 9 picks a random one that changes on every configure, so hosts see a new plugin each time. For AU, the plugin code needs exactly one upper-case letter and the manufacturer code at least one. The manufacturer code defaults to `Manu`, which isn't yours (JUCE 9.0.6 `docs/CMake API.md`).
- **Include module headers**, such as `<juce_audio_processors/juce_audio_processors.h>`. `JuceHeader.h` is optional in a CMake project and exists only if you call `juce_generate_juce_header`.
- **CLAP comes from clap-juce-extensions, pinned to a tested commit.** JUCE 9.0.6 has no CLAP format (its `FORMATS` are `Standalone Unity VST3 AU AUv3 AAX VST LV2`). Pass `CLAP_ID` and `CLAP_FEATURES` explicitly: with no features it calls the plugin an instrument.
- **Match the bus layout to the plugin type.** An effect declares an input bus and an output bus, enabled by default. An instrument sets `IS_SYNTH TRUE` and `NEEDS_MIDI_INPUT TRUE`, returns `true` from `acceptsMidi()`, and declares output buses only. Changing `VST3_CATEGORIES` alone doesn't fix a mismatch. See [references/buses-and-plugin-types.md](references/buses-and-plugin-types.md).
- **Create parameters with a `juce::ParameterID { id, versionHint }`.** The version hint sets AU parameter ordering for Logic and GarageBand: 1 for every parameter in the first release, a higher number for each later release's additions. When the plugin has a core with a parameter table, build the layout by looping over that table. What makes a good id, and why it never changes: the `audio-parameters` skill.
- **The audio thread reads parameters through cached raw-value atomics.** Store each `getRawParameterValue(id)` pointer once, in the constructor, and `load()` it in `processBlock`. Reading the value doesn't lock; the cache saves a map lookup by string on every block. Smoothing and the rest of the real-time rules: the `audio-dsp` skill.
- **The editor never calls into the audio callback.** It reaches the audio thread through parameters, atomics or a lock-free FIFO (`juce::AbstractFifo`), never by calling the processor's DSP from a UI callback. Which thread calls what: [references/processor-and-threads.md](references/processor-and-threads.md).
- **The editor is destroyed whenever its window closes** (and may be at any other time) and created again when it reopens. Anything it must rebuild (UI state, meters' history, the selected tab) lives in the processor or its saved state, never only in the editor.
- **Return at least 1 from `getNumPrograms()`** (JUCE 9.0.6 `juce_AudioProcessor.h`: it "shouldn't be less than 1"), and make `setCurrentProgram` a no-op for a plugin without programs. Some hosts call it after restoring state; if it loads anything, it overwrites the restored project.
- **Hosts load installed bundles, not the build folder, and cache their scans.** Renaming the product (`PRODUCT_NAME`, which names the bundle files) leaves the old bundles installed, so the host can list both. Installing and clearing caches are outside this skill.

## Editors

- **WebView editor:** leave the page, the resource provider, relays, attachments and the binding checker to the `audio-juce-webview` skill. This skill covers only what the processor owes any editor (above).
- **Component-based editor** (JUCE sliders, attachments, `LookAndFeel`, layout): not covered by these skills. Use JUCE's own documentation at <https://docs.juce.com> and the plugin demos in the JUCE checkout's `examples/Plugins/` folder.

## References

Read only what the task needs:

- [references/cmake-and-formats.md](references/cmake-and-formats.md): finding JUCE, the `juce_add_plugin` options that matter, plugin codes, module headers, CLAP through clap-juce-extensions, and other CMake defaults that bite.
- [references/buses-and-plugin-types.md](references/buses-and-plugin-types.md): bus layouts and flags for effects, instruments and MIDI effects, and the "listed as an effect" and "no input" failures.
- [references/processor-and-threads.md](references/processor-and-threads.md): the parameter tree, which thread calls what, the editor's lifecycle, state, programs, and host-facing pitfalls.

## Pitfalls

- No `PLUGIN_CODE`: every configure makes a new plugin, and automation and projects stop finding the old one.
- Two plugins built from one template that still share its plugin code: hosts treat them as one plugin.
- `AudioProcessor()` with no `BusesProperties`: its default input and output buses are disabled, so an effect gets silence.
- An instrument with `IS_SYNTH TRUE` but an explicit `AU_MAIN_TYPE kAudioUnitType_Effect` or `VST3_CATEGORIES Fx` left over from an effect template.
- Omitting `CLAP_FEATURES`, so the CLAP build of an effect shows up as an instrument.
- A processor that keeps a pointer to its editor. Use `getActiveEditor()` on the message thread, or better, let the editor pull from the processor.
- Testing a change in a host that still loads last week's installed bundle.

## Sources

JUCE 9.0.6 (`docs/CMake API.md`, `extras/Build/CMake/JUCEUtils.cmake`, `juce_audio_processors_headless/processors/juce_AudioProcessor.h` and `juce_AudioProcessorParameter.h`, `juce_audio_processors/utilities/juce_AudioProcessorValueTreeState.h`) and clap-juce-extensions at commit `3837f4a6ed2ab0ba46aba69ae5b7041c7c64ce74` (`README.md`, `cmake/ClapTargetHelpers.cmake`), paraphrased. Each reference lists the exact sources for its facts.
