# Plugin evals

Behavioural evals for the skills in this plugin, run with `claude plugin eval`. They check that each skill fires on a realistic prompt, stays silent when it shouldn't, and gives its key advice. They don't build plugins: real builds are checked locally by the example check script.

## Run

From the repo root:

```bash
claude plugin eval . --scaffold --allow-tools Bash Write Edit --no-publish
```

- `--scaffold` is required. Each case builds its starting project with `scaffold.sh`, which runs in the agent's working directory.
- `--allow-tools Bash Write Edit` is required. Without it, "must not write" graders pass trivially because the writes were denied.
- For a cheap smoke run, add `--runs 1 --ablation none`. To filter, use `--case 'audio-dsp-*'`.

## Cases

| Case | Checks |
|---|---|
| `audio-parameters-add-parameter` | Adding a mix parameter to a released tilt EQ fires `audio-parameters`. One grader per advice item: stable id, range/skew/unit, automatable, append with a fixed MPC count, harmless parameter 0, host ignores defaults/steps/text-to-value, effects get no MIDI, Knob FX mapping, versioned state that still loads, presets by id, and a parameter spec row. Edits nothing. |
| `audio-parameters-rename-migration` | Renaming Drive and removing Tone in a released plugin: keeps the `drive` id, keeps Tone's slot or retires its id without renumbering, migrates saved state, and notes the MPC's index-based Knob FX mapping and programs. Edits nothing. |
| `audio-parameters-not-triggered` | A Claude Code plugin settings and CLI `--timeout` question doesn't fire `audio-parameters`. |
| `audio-dsp-review-callback` | Reviewing a saturator's JUCE and MPC callbacks fires `audio-dsp`. One grader per advice item: no allocation, locks, I/O or logging including in the core, denormals, smoothing, aliasing and oversampling, latency reporting, variable block sizes (32 to 512 on the MPC), a CPU budget per target, and running the real-time checker on wrappers and core. Edits nothing. |
| `audio-dsp-plan-dsp` | Planning a tape saturator's DSP for desktop and MPC fires `audio-dsp` and covers the architecture checklist (signal chain, channel layout, latency, oversampling, sample-rate dependence, CPU budget), with no planning phases, step order or document templates. |
| `audio-dsp-not-triggered` | A Python WAV-to-FLAC batch converter question doesn't fire `audio-dsp`. |
| `audio-portable-core-share-dsp` | Sharing a JUCE compressor's DSP with a new MPC plugin fires `audio-portable-core`. One grader per advice item: header-only standard-library core, relative includes (and why the SDK build needs them), no host types in the core, the real-time marker, parameter ids and order defined once, and running the core-purity checker. Edits nothing. |
| `audio-portable-core-desktop-only` | Organising a desktop-only JUCE reverb doesn't fire `audio-portable-core`. |
| `audio-portable-core-mpc-only-sdk` | Inside a stand-in SDK checkout (the SDK's top-level layout, an empty `tools/`, one plugin project), an MPC-only plugin question doesn't fire `audio-portable-core`. |
| `audio-juce-setup-plugin` | Setting up a JUCE 9 wrapper (VST3, AU, CLAP) for a saturation core fires `audio-juce`. One grader per advice item: JUCE found through a cache or environment variable, fixed plugin and manufacturer codes (random code if left out, AU upper-case rules), module headers rather than `JuceHeader.h`, CLAP through a pinned clap-juce-extensions, an input bus for an effect, `ParameterID` with a version hint built from the core's table, cached raw-value atomics, an editor that never calls the audio callback, an editor recreated on close, at least one program with a no-op `setCurrentProgram`, and installed bundles and cached scans. No workflow, and no repeat of `audio-parameters` or `audio-dsp`. Edits nothing. |
| `audio-juce-no-input` | A delay effect built on the default `AudioProcessor()` constructor gets no input: fires `audio-juce`, names the disabled-by-default buses and the `BusesProperties` fix. Edits nothing. |
| `audio-juce-appears-twice` | A renamed compressor with no `PLUGIN_CODE` shows up twice: fires `audio-juce`, names the random plugin code and the old installed bundles and cached scans. Edits nothing. |
| `audio-juce-instrument` | Turning an effect project into a synth fires `audio-juce` and covers `IS_SYNTH`, `NEEDS_MIDI_INPUT` and `acceptsMidi`, output-only buses, CLAP instrument features, and the listed-as-effect pitfall that `VST3_CATEGORIES` alone doesn't fix. |
| `audio-juce-webview-handoff` | Wiring a new knob in a JUCE WebView editor fires `audio-juce-webview`, which gives the relay, attachment and state-request details. |
| `audio-juce-webview-add-editor` | Adding a WebView editor (knob, toggle, dropdown, a native-function button, a meter) to a JUCE 9 effect fires `audio-juce-webview`. One grader per advice item: the resource provider and its `/` root, an explicit URL map with MIME types, the interop library from the same JUCE version (one file), an ES-module import, relays registered with native integration on, member order, matching state types, listeners with no arguments, slider gestures, the silent "unknown to the backend" warning, native integration and navigation kept to the plugin's page, message-thread callbacks and events after the first load, and running the binding checker. No workflow, and no repeat of `audio-parameters` or `audio-dsp`. Edits nothing. |
| `audio-juce-webview-frozen-knobs` | A page that requests `"Drive"` for the relay `"drive"` and reads a toggle relay with `getSliderState`: fires `audio-juce-webview`, names both mismatches, explains the silent console warning, recommends the binding checker, and proposes none of the JUCE 8 fixes 9.0.6 doesn't need. Edits nothing. |
| `audio-juce-webview-blank-page` | A provider that strips the slash and never answers `/`: fires `audio-juce-webview`, names the root request and the fix, and doesn't recommend a file URL. Edits nothing. |
| `audio-juce-webview-automation-not-recorded` | A page that sets the slider's value with no drag start or end: fires `audio-juce-webview`, names the missing gesture calls, and explains why the toggle records. Edits nothing. |
| `audio-juce-webview-windows` | A WebView2 question fires `audio-juce-webview`, which says Windows isn't covered yet and gives no WebView2 advice. |
| `audio-juce-webview-not-web-slider` | A plain web page with a volume slider doesn't fire `audio-juce-webview`. |
| `audio-juce-component-editor` | A Component-based editor question fires `audio-juce`, which says Component editors aren't covered, points to JUCE's documentation, and gives no Component-specific advice. |
| `audio-juce-mpc-only-sdk` | Inside a stand-in SDK checkout, an MPC-only plugin question doesn't fire `audio-juce`. |
| `audio-juce-not-iplug2` | An iPlug2 plugin question doesn't fire `audio-juce`. |
| `audio-juce-not-nih-plug` | A nih-plug plugin question doesn't fire `audio-juce`. |
| `audio-skills-not-for-claude-code-plugin` | Building a Claude Code plugin fires no `audio-*` skill. |
| `audio-skills-not-for-cowork-plugin` | Building a Cowork plugin fires no `audio-*` skill. |

## Sandbox notes

- The agent runs with an isolated home directory, so toolchains installed under `~` are not visible, and package downloads are blocked. Cases use small scaffolded source trees and no toolchains.
- Case `env` keys must start with `EVAL_`, so `$MPC_SDK` can't be passed through. MPC cases use a stand-in scaffold that mimics an SDK checkout's layout without any SDK files.
