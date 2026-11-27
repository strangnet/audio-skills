# 03: The MPC's hard rules and routing to sibling skills

Status: done
Spec: [mpc](../../mpc.md)
Blocked by: 01

## Delivers
The skill's hard-rule summary, including the four one-line rules it shares with `audio-parameters`, each citing its SDK source at the pinned commit, and its topic-to-document table. The New effect eval case and three routing cases are written. An inspection confirms the tilt-EQ MPC wrapper keeps every rule the skill states.

## Scenarios
- when `audio-mpc` fires, its advice covers every hard-rule item
- an audio-callback question on the MPC → `audio-dsp`, named not repeated
- a parameter, Knob FX, MPC Sample or preset question on the MPC → `audio-parameters`, with only the four one-line rules in `audio-mpc`
- sharing DSP between the MPC wrapper and a JUCE wrapper → `audio-portable-core`

## Where each scenario is covered

- every hard-rule item when `audio-mpc` fires: `skills/audio-mpc/SKILL.md` ("The MPC's hard rules") and `references/hard-rules.md`; eval `audio-mpc-new-effect`, one LLM grader per item plus `tool_used` that `audio-mpc` fired
- audio callback → `audio-dsp`: eval `audio-mpc-route-audio-callback`; the skill names `audio-dsp` for the callback, block sizes, sample rate, CPU and denormals and states none of them
- parameters, Knob FX, MPC Sample, presets → `audio-parameters`: eval `audio-mpc-route-parameters`; the skill holds only the four one-line rules, each with its SDK source and a pointer to `audio-parameters`
- sharing DSP with a JUCE wrapper → `audio-portable-core`: eval `audio-mpc-route-portable-core`; the skill only names it

## Inspection: the tilt-EQ MPC wrapper keeps every hard rule

Checked `examples/tilt-eq/mpc/plugin.json`, `mpc/src/TiltEq.cpp`, `core/tilt_eq.h` and `check.py` against each rule in `skills/audio-mpc/references/hard-rules.md`. Result: **passes, no rule broken**; the example is unchanged.

- **Finished plugin, built by the build tool:** the repo holds only the project (`plugin.json`, `src/TiltEq.cpp`, `ui.json`); no hand-made `<Manufacturer> - VST - <Name>` folder is committed, and `build/` is ignored. `check.py` builds it with `<sdk>/tools/build.py` (`--target all`, so native, arm32 and arm64, with skins from `ui.json`, `version.xml`, and the SDK's validation).
- **Names agree:** `plugin.json` `name` "Tilt EQ" and `manufacturer` "strangnet" equal `PluginInfo` `name` "Tilt EQ" and `vendor` "strangnet"; the build tool names the folder from them.
- **Four-character id:** `uid` "StTl" equals `MPC_FOURCC('S', 't', 'T', 'l')`.
- **Plugin kind:** `kind` "effect" and `isInstrument = false`; nothing uses MIDI (`wantsMidi` and `sendsMidi` stay false).
- **Parameter 0 harmless:** index 0 is Output, a trim defaulting to 0 dB and smoothed in the core; the wrapper reacts to no parameter write.
- **Knob FX mapping:** `shortName` "Tilt EQ", `knobs` Tilt (1) and Output (0), labels of 8 characters or fewer, `shiftKnobs` empty (allowed: the MPC Sample hides its SHIFT indicator). `check.py` checks the mapping too.
- **Ids permanent:** ids and order come from the core's table (`output`, `tilt`), shared with the JUCE wrapper; version 0.1.0 is unreleased, so nothing has changed since a release.
- **Device setup:** a hand-over fact for the user, not something code can keep; nothing in the example contradicts it.
- **Done means passing:** `check.py` runs the build with its validation and `host_sim test` on the native build, failing on any `FAIL` line.
- **Nothing proprietary:** the wrapper includes only the SDK's `mpc_plugin.h` (from the SDK's include path, not copied) and the core; no firmware or Steinberg files.
