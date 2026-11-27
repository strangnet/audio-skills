# Buses and plugin types

How a host files a plugin (effect, instrument, MIDI effect) and what audio and MIDI it sends depend on several settings at once: CMake flags, the processor's buses, its MIDI methods and, for CLAP, the feature list. They must all agree. Facts checked against JUCE 9.0.6; see Sources.

## What each setting controls

| Setting | Where | Controls |
|---|---|---|
| `IS_SYNTH` | `juce_add_plugin` | The derived AU type (`kAudioUnitType_MusicDevice`, `aumu`) and VST3 categories (`Instrument Synth`). In the VST3 wrapper, every output bus becomes a main bus. In the AU wrapper, the host can't add or remove input buses. |
| `NEEDS_MIDI_INPUT` | `juce_add_plugin` | Whether the VST3 has an event (MIDI) input bus and the AU accepts MIDI. Without it, a VST3 instrument has no MIDI input at all. For a non-synth, it also turns the derived AU type into `kAudioUnitType_MusicEffect`. |
| `IS_MIDI_EFFECT` | `juce_add_plugin` | The derived AU type `kAudioUnitType_MIDIProcessor`. |
| `VST3_CATEGORIES`, `AU_MAIN_TYPE` | `juce_add_plugin` | Override the derived values. Leave them unset unless you mean to override. |
| `BusesProperties` | processor constructor | The audio buses, their default layouts and whether each is enabled by default. |
| `acceptsMidi()`, `producesMidi()`, `isMidiEffect()` | processor | What the processor reports. Return constants that match the CMake flags. |
| `isBusesLayoutSupported` | processor | Which layouts the host may choose. The default accepts any. |
| `CLAP_FEATURES` | `clap_juce_extensions_plugin` | How CLAP hosts file the plugin. Defaults to `instrument`. |

## Effect

- CMake: `IS_SYNTH FALSE`, `NEEDS_MIDI_INPUT FALSE` (unless it really reads MIDI), CLAP features starting with `audio-effect`.
- Constructor: an input bus and an output bus, both enabled by default:

  ```cpp
  : AudioProcessor (BusesProperties()
                        .withInput  ("Input",  juce::AudioChannelSet::stereo(), true)
                        .withOutput ("Output", juce::AudioChannelSet::stereo(), true))
  ```
- `isBusesLayoutSupported`: accept every layout the DSP can handle (usually mono and stereo with input matching output), and reject the rest.

**"The effect gets no input."** Usual causes, most common first:
1. The processor calls the default `AudioProcessor()` constructor. Its input and output buses exist but are disabled by default.
2. The constructor declares only an output bus, or passes `false` as the input bus's last argument.
3. `IS_SYNTH TRUE` (often from a synth template), so AU hosts load it as an instrument with no audio input.
4. `isBusesLayoutSupported` rejects the layout of the host's track, for example a mono track when only stereo is accepted.

## Instrument

- CMake: `IS_SYNTH TRUE` and `NEEDS_MIDI_INPUT TRUE`. Leave `VST3_CATEGORIES` and `AU_MAIN_TYPE` unset so JUCE derives `Instrument Synth` and `kAudioUnitType_MusicDevice`, or set them to instrument values. CLAP features: `instrument` plus, say, `synthesizer`.
- Processor: `acceptsMidi()` returns `true`.
- Constructor: output buses only:

  ```cpp
  : AudioProcessor (BusesProperties().withOutput ("Output", juce::AudioChannelSet::stereo(), true))
  ```
- `processBlock`: with no input, the buffer's channels may hold garbage, so clear them (or overwrite every sample) before rendering. Incoming MIDI arrives in the `MidiBuffer` argument, timestamped in samples from the start of the block. Whatever is left in that buffer when `processBlock` returns is the plugin's MIDI output, so clear it if the plugin produces no MIDI.

**"The host lists my instrument as an effect" or "it gets no MIDI".** A plugin built from an effect template usually keeps some effect setting. Check every row of the table above, not just one:
- `IS_SYNTH` still `FALSE`, or an explicit `AU_MAIN_TYPE kAudioUnitType_Effect` or `VST3_CATEGORIES Fx` left in `CMakeLists.txt`.
- An input bus still declared in the constructor. Some hosts file a plugin with a main audio input as an effect.
- `NEEDS_MIDI_INPUT` missing, so the VST3 has no MIDI input bus and the AU takes no MIDI, whatever `acceptsMidi()` returns.
- `CLAP_FEATURES` still `audio-effect`.

Changing `VST3_CATEGORIES` alone fixes none of the others: the AU type, the buses, the MIDI input and the CLAP features stay wrong. After fixing, the host still shows its cached scan until it rescans the plugin; see [processor-and-threads.md](processor-and-threads.md).

## MIDI effect

`IS_MIDI_EFFECT TRUE`, `NEEDS_MIDI_INPUT TRUE`, `NEEDS_MIDI_OUTPUT TRUE`, `isMidiEffect()`, `acceptsMidi()` and `producesMidi()` returning `true`, and CLAP feature `note-effect`. Hosts treat MIDI effects very differently from each other; test in each host you support.

## Sources

- JUCE 9.0.6 `docs/CMake API.md`: `IS_SYNTH`, `NEEDS_MIDI_INPUT`, `NEEDS_MIDI_OUTPUT`, `IS_MIDI_EFFECT`, `VST3_CATEGORIES`, `AU_MAIN_TYPE`.
- JUCE 9.0.6 `extras/Build/CMake/JUCEUtils.cmake`: how `VST3_CATEGORIES` and `AU_MAIN_TYPE` are derived when unset.
- JUCE 9.0.6 `modules/juce_audio_plugin_client/juce_audio_plugin_client_VST3.cpp`: the event bus exists only with MIDI input enabled; output bus types for synths. `juce_audio_plugin_client_AU_1.mm`: synths can't change their input bus count.
- JUCE 9.0.6 `modules/juce_audio_processors_headless/processors/juce_AudioProcessor.h` and `.cpp`: the default constructor's disabled buses, `BusesProperties`, `isBusesLayoutSupported`, the MIDI methods, and `processBlock`'s notes on garbage in output-only channels and on MIDI left in the buffer.
- JUCE 9.0.6 `examples/Plugins/AUv3SynthPluginDemo.h` and `SamplerPluginDemo.h`: instruments declared with an output bus only.
- clap-juce-extensions at commit `3837f4a6ed2ab0ba46aba69ae5b7041c7c64ce74`: `cmake/ClapTargetHelpers.cmake` (default features), `clap-libs/clap/include/clap/plugin-features.h` (feature names).
