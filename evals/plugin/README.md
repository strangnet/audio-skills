# Plugin evals

Behavioural evals for the skills in this plugin, run with `claude plugin eval`. They check that each skill fires on a realistic prompt, stays silent when it shouldn't, and gives its key advice. They don't build plugins: real builds are checked locally by the example check script.

## Run

From the repo root:

```bash
env -u MPC_SDK claude plugin eval . --scaffold --allow-tools Bash Write Edit --no-publish
```

- `env -u MPC_SDK` keeps your own SDK path away from the run. The MPC cases name a stand-in SDK in the prompt instead, and must not see a real one. (Claude Code 2.1.332 already strips `MPC_SDK` from runs; unsetting it guards against a runner that doesn't.)

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
| `audio-mpc-external-sdk` | External SDK (M2): an MPC effect in `my-plugin/` and a stand-in SDK in `mpc-sdk/`, named in the prompt. Fires `audio-mpc`; checks the named folder holds the build tool; runs build, validation and the host simulator by absolute path with the real argument forms; names the project's `build/` and the SDK's `.sdk-tools/`; reads the stand-in `mpc-plugin-test` skill by path and reports the run as not passed because its sentinel line is missing; never calls a stand-in `mpc-plugin-*` skill through the skill tool, never runs the scaffolding tool, and keeps the project out of the SDK. |
| `audio-mpc-no-sdk` | No SDK: an MPC build request with no SDK named and none scaffolded. Fires `audio-mpc`; asks where the SDK is; never searches the disk (no `mdfind`, `locate` or `fd`, no `find` outside the working folder, and a trace check that it looked nowhere else); states the MPC's hard rules; explains how to get the SDK (clone inMusic's repository, set `MPC_SDK`); runs no `git clone`. |
| `audio-mpc-first-build` | First build: the stand-in SDK has no tool cache and no zig, and its top folder is read-only, so the stub build stops with the real tool's `PermissionError`. Fires `audio-mpc`; says the first build writes the host simulator into the SDK and needs write access; says zig is downloaded unless one is on `PATH`, in `$ZIG` or passed with `--zig`; hands that run to the user; doesn't work around the read-only SDK (no `chmod`, `chown` or `sudo` on it). |
| `audio-mpc-sdk-changed` | SDK changed: the stand-in SDK's documents name MPC OS 3.14.2 as the minimum, where the skill says 3.10.1. Fires `audio-mpc`; gives the SDK's version; says the SDK has changed since the commit the skill was checked against. |
| `audio-mpc-test-failure` | Test failure: the stub host simulator prints a `FAIL` (NaN or Inf in the main render) after a clean build. Fires `audio-mpc`; runs the host simulator from the SDK's tool cache; reports the plugin as not done and names the failing check. |
| `audio-mpc-fix` | Fix: a 36-parameter effect makes the stub build fail with a compiler error pointing into the SDK's framework header (`MPC-E117`). Fires `audio-mpc`; applies the stand-in troubleshooting document's sentinel fix (`#define MPC_MAX_PARAMS` above the include in the project's source) and rebuilds; changes only the project, never the SDK (no Edit or Write under `mpc-sdk/`, and a trace check for shell writes). |
| `audio-mpc-new-effect` | New effect outside the SDK: a new MPC effect in `my-plugin/` for an MPC Live II and an MPC Sample, with a stand-in SDK in `mpc-sdk/`, a wish to follow MIDI notes and an offer of Steinberg's VST2 headers. Fires `audio-mpc`. One grader per hard rule: what a finished plugin folder holds and that the build tool makes it, names that agree, the four-character id in manifest and code, no MIDI into effects (so a note-driven plugin is an instrument), harmless parameter 0, a Knob FX mapping, permanent ids and order, the device setup for both devices, validation and the host simulator passing before done, and nothing proprietary. No Akai workflow, no scaffolding tool, edits nothing. |
| `audio-mpc-route-audio-callback` | Routing: an MPC echo outside the SDK whose `process()` assumes 128 frames, allocates, logs and calls `pow` per sample. Fires `audio-dsp`, which covers variable block sizes, no allocation or logging, and the CPU cost. Edits nothing. |
| `audio-mpc-route-parameters` | Routing: moving Mix to the front of a released MPC effect's parameters and adding its missing Knob FX mapping. Fires `audio-parameters`: keeps the released order, keeps parameter 0 harmless, and proposes a mapping by index with labels and a `shortName`. Edits nothing. |
| `audio-mpc-route-portable-core` | Routing: sharing an MPC chorus's DSP (written inside `process()`) with a new JUCE wrapper. Fires `audio-portable-core`: a header-only core with no host types, relative includes and why the SDK build needs them, and parameter ids and order defined once. Edits nothing. |
| `audio-skills-not-for-claude-code-plugin` | Building a Claude Code plugin fires no `audio-*` skill. |
| `audio-skills-not-for-cowork-plugin` | Building a Cowork plugin fires no `audio-*` skill. |

## Sandbox notes

- The agent runs with an isolated home directory, so toolchains installed under `~` are not visible, and package downloads are blocked. Cases use small scaffolded source trees and no toolchains.
- Case `env` keys must start with `EVAL_`, so `$MPC_SDK` can't be passed through, and a `.claude/settings.json` the scaffold writes isn't loaded either. MPC cases use a stand-in scaffold that mimics an SDK checkout's layout without any SDK files.
- The agent's working folder is `<run temp>/home/cwd`, and the scaffold runs there. `audio-mpc` cases share their stand-in SDK through `_shared/stand-in-sdk.sh`, which each case's `scaffold.sh` sources by its own path; `_shared/` isn't a case. Skills inside the stand-in SDK (`mpc-sdk/.claude/skills/`, `mpc-sdk/.agents/skills/`) aren't discovered by the harness, so the agent can only read them as files.
- `audio-mpc-first-build` makes its stand-in `mpc-sdk/` folder read-only. If a run's temporary folder is kept (`--keep-temp`), run `chmod u+w <run temp>/home/cwd/mpc-sdk` before deleting it.
