# Processor, threads and host-facing behaviour

Facts checked against JUCE 9.0.6; see Sources. Parameter design (ids, ranges, automation, state versions) belongs to the `audio-parameters` skill, and real-time rules for the callback to the `audio-dsp` skill. This file gives only the JUCE API for them.

## The parameter tree

- Hold parameters in a `juce::AudioProcessorValueTreeState` built from a `ParameterLayout`. When the plugin has a portable core with a parameter table, build the layout by looping over the table, so the JUCE ids and order can't drift from the other target's:

  ```cpp
  for (const auto& p : core::kParams)
      layout.add (std::make_unique<juce::AudioParameterFloat> (
          juce::ParameterID { p.id, 1 }, p.name,
          juce::NormalisableRange<float> (p.min, p.max), p.def));
  ```
- **`juce::ParameterID { id, versionHint }`.** The version hint exists for Logic and GarageBand, which address AU parameters by index. JUCE's AU wrapper sorts parameters by version hint, then by a hash of the id. Give every parameter of the first release hint 1, and every parameter added in a later release a hint higher than any before it. A hint of 0 counts as unset, and AU debug builds may check at runtime that it was set. Adding or removing a parameter whose hint is below the highest one breaks saved automation in those hosts.
- AUv3 has no such ordering control. That format is out of scope here.

## Reading parameters on the audio thread

- `getRawParameterValue (id)` returns a `std::atomic<float>*` holding the parameter's plain (denormalised) value. Reading it doesn't lock.
- The call itself looks the id up in a `std::map` keyed by string. Do it once, in the constructor, and keep the pointers (an array indexed like the core's table works well). In `processBlock`, call `load()` on each cached pointer once per block.
- Inside an `AudioProcessorValueTreeState::Listener::parameterChanged` callback, the raw value isn't guaranteed to be up to date yet: use the `newValue` argument.

## Which thread calls what

| Call | Thread | Consequence |
|---|---|---|
| `processBlock` | The host's audio thread | Real-time rules apply (see `audio-dsp`). Never touch the editor or any UI from here. |
| `prepareToPlay`, `releaseResources` | Called by the host before playback starts and after it stops | Allocate and size buffers here. The announced block size is a strong hint, not a promise: blocks can vary, and a buggy host can exceed it. |
| `AudioProcessorParameter::setValue` (host automation) | Any thread, at any time, including during `processBlock` | A custom parameter class's `setValue` must be fast and lock-free. |
| `AudioProcessorParameter::Listener` and `AudioProcessorValueTreeState::Listener` callbacks | Synchronously, on whichever thread changed the parameter, often the audio thread | Keep them tiny and lock-free. To reach the message thread, trigger an `AsyncUpdater` or have the editor poll on a timer. |
| `acceptsMidi`, `producesMidi`, `isMidiEffect` | May be the audio thread | Return constants. |
| `getStateInformation`, `setStateInformation` | Not guaranteed to be the message thread | `AudioProcessorValueTreeState::copyState` and `replaceState` are thread-safe for this, but they lock, so never call them from `processBlock`. |
| `createEditor`, the editor's methods, `getActiveEditor` | The message thread | `getActiveEditor` is only safe on the message thread, because the message thread may delete the editor. |

**The editor never calls into the audio callback** and never runs the DSP itself. It changes parameters (the host then sees the change and can record it), writes atomics the audio thread reads, or pushes into a single-reader, single-writer lock-free FIFO (`juce::AbstractFifo` manages one). Data flowing back (meters, scopes) goes the same way in reverse: the audio thread writes atomics or a FIFO, and the editor reads them on a timer.

## The editor's lifecycle

- There is no editor until the user opens one, and they may never open one. The processor must work without it.
- The host can delete the editor whenever its window closes and create a new one when it reopens. The editor is always deleted before its processor.
- So the editor holds nothing that matters beyond its own lifetime. Anything it needs to rebuild (window size, selected page, a meter's history, the state of a control that isn't a parameter) lives in the processor or in the processor's saved state, and the new editor reads it in its constructor.
- The processor never keeps a raw pointer to its editor: it can become dangling at any time.
- WebView editors: the `audio-juce-webview` skill covers the page, relays and attachments. Component-based editors aren't covered by these skills; see JUCE's documentation and its `examples/Plugins/` demos.

## State and programs

- Save the whole state in `getStateInformation` and restore it in `setStateInformation`. With an `AudioProcessorValueTreeState`, that's `copyState()` written as XML, and `replaceState()` after checking the root tag. Put a format version in it from the first release; how to version and migrate is in `audio-parameters`.
- `getNumPrograms()` must return the same value for the processor's whole life, and JUCE's documentation says it shouldn't be less than 1. A plugin without programs returns 1, `getCurrentProgram()` returns 0, and `setCurrentProgram`, `getProgramName` and `changeProgramName` do nothing.
- Keep `setCurrentProgram` a no-op unless the plugin really has built-in programs. Some hosts call it after restoring a project's state, and a version that loads defaults or a preset there wipes the restored state.

## Host-facing behaviour

- **Hosts load installed bundles, not the build folder.** On macOS a host scans the system and user plug-in folders, not your build tree. A fresh build changes nothing in the host until the new bundle is installed (for example with `COPY_PLUGIN_AFTER_BUILD TRUE`).
- **Hosts cache their scans.** After changing the plugin's type, buses, MIDI flags or codes, the host may keep showing the old description until it rescans.
- **Renaming the product leaves the old bundles installed.** A new `PRODUCT_NAME` produces new bundle files next to the old ones, so the host can list the plugin twice, or load the old one. A changed plugin code, manufacturer code or bundle id has the same effect.
- **"The plugin appears twice."** Besides an old bundle from a rename, check for two plugins that share a plugin code (copied from one template), and for a plugin code that changes on every configure because `PLUGIN_CODE` is missing. A host that lists both the VST3 and the AU of one plugin is behaving normally.
- Installing plugins, clearing host caches and signing for local tests are outside this skill.

## Sources

- JUCE 9.0.6 `modules/juce_audio_processors_headless/utilities/juce_AudioProcessorParameterWithID.h`: `ParameterID` and its version hint.
- JUCE 9.0.6 `modules/juce_audio_processors_headless/processors/juce_AudioProcessorParameter.h`: the version-hint rules and rationale, `setValue` threading, listener threading.
- JUCE 9.0.6 `modules/juce_audio_plugin_client/juce_audio_plugin_client_AU_1.mm`: parameters sorted by version hint.
- JUCE 9.0.6 `modules/juce_audio_processors/utilities/juce_AudioProcessorValueTreeState.h` and `.cpp`: `getRawParameterValue` (plain value, `std::map` lookup), `copyState` and `replaceState` (thread-safe but locking), listener caveat.
- JUCE 9.0.6 `modules/juce_audio_processors_headless/processors/juce_AudioProcessor.h`: `prepareToPlay`, `processBlock`'s threading note, the MIDI methods, `createEditor`'s notes on the editor's lifecycle, `getActiveEditor`, `getNumPrograms` ("shouldn't be less than 1", constant for the processor's life).
- JUCE 9.0.6 `modules/juce_core/containers/juce_AbstractFifo.h`: single-reader, single-writer lock-free FIFO.
- JUCE 9.0.6 `docs/CMake API.md`: `COPY_PLUGIN_AFTER_BUILD`.
- The program-reset host behaviour comes from field reports collected in the Plugin Freedom System's troubleshooting notes, not from JUCE's documentation.
