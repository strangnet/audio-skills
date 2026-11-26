---
name: audio-parameters
description: Parameter, saved-state and preset know-how for audio plugins that ship to desktop (JUCE VST3, AU, CLAP) and to Akai MPC hardware, including the parameter spec table, stable ids, ranges and skew, automation, the MPC host's parameter rules and Knob FX mapping, versioned state and migrations. Use when adding, changing, renaming, reordering or removing a plugin parameter; designing a parameter list or parameter spec; choosing ranges, skew, units, defaults or smoothing; deciding what can be automated; writing state save and load, presets or built-in programs; or changing a released plugin in a way that could break saved projects, automation or presets. Not for work inside an Akai MPC SDK checkout that Akai's own `mpc-plugin-dsp` or `mpc-plugin-presets` skills already cover (use those there). Not for Claude Code or Cowork plugin settings, agent-plugin manifests, or command-line parameters and flags.
---

# Audio parameters

A plugin's parameters are a public contract. Hosts store automation against them, projects and presets store their values, and on the MPC users map hardware knobs to them. Once a version is released, every id, index and range in that contract is somebody's saved data. Design the list as if it can never change, because in practice it can only grow.

## Rules

- **Ids are stable forever and never reused.** A parameter's id (a short machine string such as `tilt` or `out_gain`) is what saved state, presets and JUCE automation are keyed on. Change the display name as often as you like; never change the id after release, and never give a retired id to a new parameter. An old project would load its value into the wrong control.
- **Order is part of the contract too.** The MPC addresses parameters by index (Knob FX mapping, built-in programs, default Q-Link assignment), and some hosts do as well. Append new parameters at the end. Never reorder, insert or delete in the middle of a released list.
- **Define each parameter in real units.** State the plain range (20 to 20000 Hz, -24 to +24 dB), the default, the unit and the curve. Hosts see a normalised 0 to 1 value; the curve maps it. Frequencies and times want a log or skewed curve so the useful range isn't squashed into the bottom of the knob; gains in dB and pans are usually linear. Changing a released range or curve changes what old automation and old normalised values mean: treat it as breaking.
- **Decide what can be automated.** Sound-shaping controls (gain, cutoff, mix, tilt) should be automatable and smoothed. Controls that reallocate, restructure or change latency (oversampling factor, FFT size, buffer length, a mode that rebuilds the graph) should not be automatable, or must be safe to change at audio rate. Every automatable parameter needs a smoothing time so automation can't click.
- **Saved state carries a version, and every old version still loads.** Write a format version into state from the first release. On load, read the version and convert old layouts forward; never refuse or silently reset an old project. Unknown ids in old state are ignored; ids missing from old state get their defaults.
- **Presets reference parameters by id, not by index.** Store a preset as id → plain value. Where a target forces index order (MPC built-in programs), generate that list from the id-keyed source in the spec's row order, so it can't drift.
- **Removing or renaming a released parameter: keep the old id and migrate.** Never renumber. A rename changes only the display name. A removal keeps the id (and, on the MPC, its index slot) as an inert, non-automatable parameter, or retires the id permanently; saved state is converted by a migration keyed on the state version. If a parameter's meaning or range must change, add a new id at the end and migrate the old value into it.

## The MPC in one paragraph

The MPC host reads the parameter count once at load, so the list is fixed at build time. On every prepare it nudges parameter 0 to an extreme and back, so row 0 must be harmless (an output trim, never a trigger, panic or reset). It ignores the plugin's defaults, step counts and text-to-value conversion. Effects receive no MIDI. Every effect needs a Knob FX mapping in `plugin.json` for the MPC Sample, whose six knobs are that plugin's entire UI. Details, sources and consequences: [references/mpc-constraints.md](references/mpc-constraints.md).

## References

Read only what the task needs:

- [references/parameter-spec-format.md](references/parameter-spec-format.md): the parameter spec table (columns, rules, a worked example). Read when designing or changing a parameter list.
- [references/mpc-constraints.md](references/mpc-constraints.md): the MPC host's parameter rules and the Knob FX mapping, with their SDK sources.
- [references/state-and-migration.md](references/state-and-migration.md): versioned state, migrations, presets by id, what counts as breaking, and the JUCE and MPC facts behind them.

## Pitfalls

- Using the display name as the id, then "fixing a typo" in the name after release.
- Deleting a parameter from the middle of the list "because nothing uses it": every later index shifts, and the Knob FX mapping and built-in programs now point at the wrong controls.
- Presets saved as arrays of values in parameter order.
- Relying on the host's default or reset for the MPC: it doesn't read the plugin's defaults.
- A bypass, mode switch or trigger as parameter 0.
- Tightening a range in a patch release: old values clip or move.
- No version in the first release's state, so the second release can't tell old projects from new ones.
