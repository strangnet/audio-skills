# State, presets and migration

Saved state is a file format. Projects saved with version 1.0 of a plugin will be opened by version 3.2, possibly years later, possibly on another target. This file covers how to keep that working.

## Versioned state

- **Write a format version from the very first release.** Without one, the next release can't tell an old project from a new one. A single integer is enough; bump it whenever the layout or meaning of stored data changes.
- **Every old version still loads.** On load, read the version, then convert forward one step at a time (1 → 2 → 3) until the data is current. Keep every converter; never delete the oldest path. Refusing to load, or silently falling back to defaults, loses the user's work.
- **Key parameter values by id.** Store each parameter as id → value, not as an array in parameter order. Then adding parameters, and even a different order on another target, can't misassign values.
- **Store plain values, or both.** A plain value (in real units) survives a range or curve change; a normalised value doesn't mean the same thing after one. The MPC SDK framework stores both and prefers plain when they disagree.
- **Tolerate what you don't know.** Ignore unknown ids (they may come from a newer version or a retired parameter). Give ids missing from old state their defaults. Clamp loaded values into the current range.
- **Load off the audio thread, apply safely.** State load runs on a non-audio thread on both targets while audio may be running. Parse and convert there, then hand the result to the audio thread without locks in the audio callback (atomics for parameters, a staged copy swapped in for anything bigger).
- **Non-parameter state** (a loaded sample's path, a sequencer pattern, a random seed) gets its own version too, inside the same blob.

## Presets reference parameters by id

- A preset is a map from parameter id to plain value, plus a name. It doesn't depend on the order or the count of parameters.
- A preset that lacks an id (because it predates that parameter) leaves it at its default. A preset with an unknown id ignores it.
- Where a target insists on index order, derive that form from the id-keyed source:
  - MPC built-in programs are `addProgram(name, { plain values in parameter order })`, matched by index. Generate the list from the id-keyed preset in the spec's row order, so a later edit can't put a value under the wrong parameter.
  - A host that stores automation per parameter index (some VST 2 and AU paths) is one more reason never to reorder.
- Program 0 on the MPC is what the device starts with and, on the MPC Sample, fixes every parameter not on a knob. Make it the defaults.

## Removing or renaming a released parameter

The rule: **keep the old id and migrate saved state; never renumber.**

| Change | Do | Don't |
|---|---|---|
| Rename | Change only the display name (and MPC label). The id stays as it was, even if it now reads oddly. | Change the id: every saved value and automation lane for it is lost. |
| Remove | Keep the parameter as an inert, non-automatable slot with the same id and index (hidden from the UI, ignored by the DSP), or, on targets that address only by id, drop it from the list but retire the id for good. Old state that contains it loads without error. | Delete it from the middle of the list: every later index shifts, and on the MPC the Knob FX mapping, built-in programs and Q-Link defaults now point at the wrong controls. |
| Change meaning, range or curve | Add a new parameter with a new id at the end. Bump the state version and, in the migration from the old version, convert the old value into the new parameter. Retire the old one as above. | Reuse the old id with a new meaning, or a retired id for a new parameter. |
| Change the default | Fine; only new instances see it. Saved projects keep their stored value. | |
| Add | Append at the end, with a new id. Old state simply lacks it and it takes its default. | Insert in the middle. |

On the MPC the parameter count is fixed when the plugin loads, but a new plugin version may have more parameters than the old one: the framework's chunk is keyed by id, so appended parameters are safe. What it can't survive is a shifted index.

## What counts as breaking

Breaking (old projects, presets or automation change or fail):

- an id renamed or reused
- a parameter removed or moved, so indices shift
- a range narrowed or moved, or a skew or curve changed (stored normalised values now mean something else; stored plain values may clip)
- a type changed (float to choice), or choices reordered or removed
- a state layout change with no version and no migration
- a DSP change that makes old presets sound different

Not breaking: a display-name change, a new default, a parameter appended at the end, new state fields that old versions didn't write.

When a breaking change can't be avoided, it is a major version for the plugin and still needs a migration for old state. With a migration in place, most "breaking" parameter changes become safe.

## JUCE facts (JUCE 9.0.6)

- `juce::ParameterID` combines a parameter's string identifier with an `int` version hint (default 0). The identifier is "a string that uniquely identifies a single parameter".
- The version hint "influences parameter ordering in Audio Unit plugins" for backwards compatibility in Logic and GarageBand. Parameters in the first release use one hint (for example 1); parameters added in each later release use a higher number than any before. Adding or removing parameters whose hint is lower than the current maximum breaks saved automation in some hosts. A hint of 0 means "not set", and AU debug builds may check that it was set.
- `AudioProcessorParameter::isAutomatable()` returns true by default, so a parameter that must not be automated has to say so.
- When a UI changes a parameter, call `beginChangeGesture()` and `endChangeGesture()` around `setValueNotifyingHost()`, or hosts can't record automation properly.
- `AudioProcessorValueTreeState::copyState()` and `replaceState()` are thread-safe but use locks, so they are not real-time safe: call them from `getStateInformation` and `setStateInformation`, never from the audio callback. Put the state version on the saved tree's root and run migrations on the tree before `replaceState()`.
- A `NormalisableRange` maps a plain range to the normalised 0..1 range and carries the skew.

## Sources

- JUCE 9.0.6 (the version in JUCE's `CMakeLists.txt` on the master branch, checked 2026-11-26): API reference for `juce::ParameterID`, `juce::AudioProcessorValueTreeState` and `juce::NormalisableRange` at docs.juce.com/master, and the doc comments in `modules/juce_audio_processors_headless/processors/juce_AudioProcessorParameter.h` and `modules/juce_audio_processors_headless/utilities/juce_AudioProcessorParameterWithID.h`.
- Akai MPC Plugin SDK 1.0 plus unreleased 1.1 changes (commit e78bad5), MIT, copyright (c) 2026 inMusic Brands, Inc.: `docs/host-contract.md` (State, Programs), `docs/presets.md`, `docs/dsp-cookbook.md` sections 7 and 8, `framework/mpc_plugin.h` (state chunk, `setProgram`).
- Plugin Freedom System (commit e965cdd), by TÂCHES (glittercowboy), MIT: `.claude/skills/plugin-improve/references/breaking-changes.md` and `versioning.md`, adapted for the breaking-change list.
