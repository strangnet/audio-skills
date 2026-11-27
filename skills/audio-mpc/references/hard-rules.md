# The MPC's hard rules

The rules a plugin must keep to load and behave on the MPC, with the SDK document each comes from. They hold whether or not the SDK is at hand. Checked against Akai's MPC Plugin Builder SDK at commit `e78bad5`. If the document at the user's `<sdk>` says something different, follow the SDK's document and tell the user the SDK has changed since that commit.

Other skills hold the detail on three topics. This file names them and doesn't repeat them:
- **`audio-dsp`**: the audio callback, real-time safety, block sizes, the fixed sample rate, the CPU budget and denormals on the MPC.
- **`audio-parameters`**: parameter ids, order and ranges, parameter 0, MIDI into effects, the Knob FX keys and the MPC Sample, the plugin id's permanence, built-in programs and presets.
- **`audio-portable-core`**: sharing one DSP core between the MPC wrapper and a JUCE wrapper.

## What a finished plugin is

A folder named `<Manufacturer> - VST - <Name>/` that holds:
- `plugin.json`, the manifest
- `version.xml`
- `VST/<slug>-arm32.so` and `VST/<slug>-arm64.so`: the 32-bit ARM library for the MPC X, Live, Live II, One, One+, Key 61, Key 37 and Force, and the 64-bit one for the MPC Live III, XL and MPC Sample
- `Plugin Skins/`, the touch UI (`TUI.json`, `Q-Links.json` and images)
- `Content/` only when the project has one (samples, wavetables and other files the plugin reads at run time)

The SDK's own documents disagree on two parts. The agent instructions list `version.xml` and `Plugin Skins/` as parts of a finished plugin (`AGENTS.md`, "What a finished plugin is"). The folder-format document calls both optional: without skins the MPC shows a generic UI of parameter sliders, and without `version.xml` the plugin counts as compatible (`docs/plugin-folder-format.md`, "The folder", "version.xml", "Plugin Skins"). What settles it in practice is the build tool: it always writes `version.xml`, and it generates `Plugin Skins/` from the project's `ui.json` (or automatic pages) unless it runs with `--no-ui` (`tools/build.py`, `make_skins` and `write_version_xml`). So a finished plugin has both, as the build tool makes it by default.

The SDK's build tool makes the folder in `<project>/build/`. Never assemble it, rename it or patch its files by hand: the build checks it with the SDK's validation as it goes, and a hand-made change skips that check. Users copy the whole folder into a folder named exactly `VST2 Plugins` at the root of a drive (`docs/plugin-folder-format.md`, "Where the folder goes on the MPC").

## Names that must agree

Three places carry the plugin's name and manufacturer, and they must be the same strings:
- `plugin.json`: `name` and `manufacturer`
- the plugin info in code: `PluginInfo::name` and `PluginInfo::vendor` (`framework/mpc_plugin.h`)
- the folder name: `<manufacturer> - VST - <name>`

The MPC builds the folder name from the strings the loaded plugin reports, and finds the skins and `version.xml` by that name. If they disagree, the plugin still loads but gets the default UI. The MPC drops these characters when it builds the name: `" # @ , ; : < > * ^ | ? \ /`, and the SDK's tools apply the same rule. Always set a manufacturer: an empty one gives a folder named `VST - <name>`. Sources: `AGENTS.md`, "Hard rules" ("Names must agree"); `docs/plugin-folder-format.md`, "The folder" and the `plugin.json` table.

Renaming a released plugin is changing its identity; see the id rule below.

## The four-character id

`plugin.json`'s `uid` and the `uniqueId` in code must be the same id. Write `uid` as a four-character string such as `"AcWb"`, and set `PluginInfo::uniqueId = MPC_FOURCC('A','c','W','b')` in code; the first character is the most significant byte. A missing or invalid `uid` makes the MPC invent one from the file path, which won't match the loaded plugin, so projects lose it later. Choose an id unlikely to clash with other plugins, such as two letters of the maker's name and two of the plugin's. The framework's default, `MPC_FOURCC('N','o','I','d')`, is a placeholder to replace.

Sources: `AGENTS.md`, "Hard rules" ("Identity is permanent"); `docs/plugin-folder-format.md`, the `plugin.json` table and "Notes on `uid`"; `framework/mpc_plugin.h`, `struct PluginInfo`. The SDK's validation reports a mismatch between the manifest's `uid` and the id the binary reports as an error (`tools/validate.py`).

## Plugin kind

A plugin is an **effect** (an insert on a track) or an **instrument** (a plugin program that makes its own sound). `plugin.json`'s `kind` and `PluginInfo::isInstrument` must say the same thing.

Effects get no MIDI, and MIDI a plugin sends is accepted by the host and then thrown away. So a sequencer, arpeggiator or anything else driven by notes is an **instrument that makes its own sound** (it can still follow the MPC's tempo and transport): it can't be an effect that reacts to notes, and it can't be a MIDI generator that plays the MPC's other tracks. The MPC Sample loads effects only, so an instrument doesn't run there.

Sources: `AGENTS.md`, "Hard rules" ("Effects get no MIDI; plugins cannot send MIDI to the MPC"); `docs/host-contract.md`, "MIDI" and "MPC Sample"; `docs/faq-and-legal.md`, the MIDI answer; `framework/mpc_plugin.h`, `PluginInfo::isInstrument` ("synth/drum machine/sequencer").

## Four rules `audio-parameters` also holds

One line each here, so the rule is stated even when `audio-mpc` is installed alone. The `audio-parameters` skill has the detail and the design consequences.

- **Parameter 0 is nudged on every load and must be harmless:** the host moves it to an extreme and straight back on every prepare, so make it an output trim with no side effects. (`docs/host-contract.md`, "Load sequence"; `AGENTS.md`, "Hard rules")
- **Effects get no MIDI:** anything an effect needs must be a parameter. (`docs/host-contract.md`, "MIDI"; `AGENTS.md`, "Hard rules")
- **Every effect ships a Knob FX mapping:** `shortName`, `knobs` and `shiftKnobs` in `plugin.json` for the MPC Sample, whose six knobs are the effect's whole UI. (`AGENTS.md`, "Hard rules"; `docs/knob-fx.md`)
- **The plugin id and parameter ids are permanent:** `uid`, parameter id strings and parameter order never change once users have projects; new parameters go at the end. (`AGENTS.md`, "Hard rules"; `docs/knob-fx.md`, "Identity is permanent")

## Device setup the user needs

Tell the user this when handing over a plugin; `AGENTS.md` says to always do so.
- **MPC (32-bit and 64-bit):** MPC OS 3.10.1 or later; earlier firmware ignores the `VST2 Plugins` folder. In Preferences → Enhancements (Beta), turn on Enable Enhancements and External Plugin Support. With either off, plugins stay hidden.
- **MPC Sample (effects only):** firmware v1.4.0 or later. In MIDI Config, in the Dev Enhancements (Beta) section, turn on Dev Enhancements (Beta) and then Custom Plug-In Support. Plugins go on its microSD card.

Sources: `AGENTS.md`, "What a finished plugin is"; `docs/supported-devices.md`, the requirements per device and the comparison table; `docs/install-and-test.md`, "Copy to the MPC"; `docs/knob-fx.md`, "What the MPC Sample supports". How to install is Akai's `mpc-plugin-deploy` skill, and only when the user asks.

## Done means validation and the host simulator pass

A plugin isn't done until the SDK's validation reports no errors (the build tool runs it unless told `--no-validate`; `tools/validate.py` runs it alone) and the host simulator's `test` run on the native build has no `FAIL` line. Fix every `FAIL` before anything goes on an MPC: the MPC has no crash protection for plugins. `WARN` lines may be intentional, but understand each one. Sources: `AGENTS.md`, "The workflow, every time" (the fact under its last line, not its step order); `docs/install-and-test.md`, "Test on your computer first"; `tools/validate.py`, usage text. The commands from outside the SDK are in `sdk-tools.md`.

## Nothing proprietary

Don't fetch, copy or depend on files from MPC firmware or from Steinberg's VST SDK, or on code whose licence doesn't fit what the user wants to do with the plugin. The SDK needs neither: its framework carries its own independent description of the VST 2.4 binary interface. Note the licence of any borrowed DSP in the project's README. Sources: `AGENTS.md`, "Hard rules" ("Nothing proprietary"); `docs/faq-and-legal.md`, the VST2 and licence answers.

## Sources

Akai's MPC Plugin Builder SDK at commit `e78bad5` (2026-11-23, changelog section "Unreleased (will become 1.1)"), MIT licence, copyright (c) 2026 inMusic Brands, Inc. Paraphrased; no long quotes.
- `AGENTS.md`: "What a finished plugin is", "Hard rules", and the last line of "The workflow, every time"
- `docs/plugin-folder-format.md`: "The folder", "Where the folder goes on the MPC", the `plugin.json` table, "Notes on `uid`", "version.xml", "Plugin Skins"
- `docs/host-contract.md`: "Load sequence" (the parameter 0 nudge), "MIDI", "MPC Sample"
- `docs/knob-fx.md`: "What the MPC Sample supports", "Identity is permanent"
- `docs/supported-devices.md`: requirements for each device, the MPC Sample
- `docs/install-and-test.md`: "Test on your computer first", "Copy to the MPC"
- `docs/faq-and-legal.md`: the MIDI, VST2 and licence answers
- `framework/mpc_plugin.h`: `MPC_FOURCC`, `struct PluginInfo`
- `tools/build.py`: `make_skins`, `write_version_xml`, `--no-ui`, `--no-validate`
- `tools/validate.py`: usage text, the `uid` check
