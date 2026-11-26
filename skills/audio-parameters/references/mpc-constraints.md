# MPC parameter constraints and Knob FX

The MPC hosts plugins through its own VST 2.4 host, and that host uses only part of the parameter interface. These are the facts that shape a parameter list for the MPC target. They are paraphrased from Akai's MPC Plugin SDK documents (see Sources); when working inside an SDK checkout, Akai's own `mpc-plugin-dsp` and `mpc-plugin-presets` skills and the SDK docs are the authority.

## What the host does with parameters

| Fact | Consequence for the design |
|---|---|
| Every parameter is a float from 0 to 1 to the host. The SDK framework maps that to real ranges, ints, bools and choices. | Describe parameters in plain units in the spec; the wrapper does the mapping. |
| **The parameter count is read once at load.** It must never change at run time. | No dynamic parameter lists. Everything a later version might need has to fit an append-only list. A parameter you remove keeps its slot. |
| **On every prepare the host nudges parameter 0** to 1.0 or 0.0 and straight back (a quirk for plugins without a native editor, which is every SDK plugin). Prepare repeats on sample-rate or block-size changes and after suspend and resume. | Parameter 0 must be harmless: an output trim or master volume, never a trigger, panic, reset, bypass or mode switch. Do nothing expensive or audible in response to any parameter write. |
| **The host does not read the plugin's defaults.** The on-screen reset uses 0 unless the skin says otherwise. | Defaults live in code and in built-in program 0. The host selects program 0 after loading, so make program 0 the "Init" sound. |
| **The host ignores extended parameter properties (step counts, integer ranges) and never calls text-to-value.** Data-wheel steps come from the skin's `replacementStrings`. | Don't rely on the host to quantise a stepped control or to parse typed values. The plugin itself must snap choices and ints. |
| The host asks "can be automated" for every parameter at load and caches the answer. Only parameters that say yes can be automated. | The spec's automatable column is what the wrapper reports; it can't change later in a session. |
| Names and value text are read from the plugin and shown on a small screen; the unit label is not appended by the host. | Keep names to about 12 characters and value text to about 8. Put the unit in the value text. |
| Parameter changes from the screen and knobs arrive on the audio thread between blocks; changes from project load, preset load and automation can arrive on the UI thread while `process` runs. | Parameter storage must be atomic; smooth audible changes; read each parameter once per block. |
| The first 16 parameters are the default Q-Link assignments and the default UI page. | Put the most played controls early, after a harmless row 0. |
| **Effects receive no MIDI at all**, and MIDI a plugin sends is discarded. | An effect can't take MIDI learn, MIDI-triggered events or note input on the MPC. Anything an effect needs must be a parameter. |

## Knob FX (MPC Sample)

The MPC Sample loads effects only, as **Knob FX**. It has no edit screen and no skins: its whole UI is six parameters, three on the knobs and three more with SHIFT held.

- **Every effect needs a Knob FX mapping** in its `plugin.json`: `knobs` and `shiftKnobs`, each an array of up to three entries `{ "parameter": <0-based index>, "label": "<text>" }`, plus an optional `shortName` of 12 characters or fewer.
- Without a mapping the knobs control parameters 0 to 5, labelled `Param 1` to `Param 6`. Parameter 0 is usually an output trim, so that default is rarely useful: always ship a mapping.
- `parameter` must be a whole number naming an existing parameter; anything else leaves the knob greyed out. Entry order is knob order. Entries after the third are ignored.
- A knob without a `label` shows `Param <n>`, not the parameter's name. Always write a label, about 8 characters (three labels share a 320-pixel screen). This is where the spec's MPC label column ends up.
- Parameters not on a knob stay at program 0's value (or the default) and cannot be changed on that device. Choose them with care.
- Bools and choices work on a knob. A switch that disables a mapped knob (Sync over Time) should itself be mapped, or default to the state that suits the mapped knob.
- **The mapping refers to parameters by index**, so it inherits the never-reorder rule. Changing which parameter a knob controls changes users' muscle memory: do it only in a new version and say so.

Akai's SDK validator (`tools/validate.py`) checks the mapping against the parameters the binary reports and prints the resolved mapping.

## Identity and state in the SDK framework

- `uid`, parameter `id` strings and parameter order must not change once users have projects. New parameters go at the end.
- The framework's state chunk is versioned: a `MPCP` tag, a format version (2 in the current framework; version 1 chunks still load), then each parameter as its id with plain and normalised values, then your extra state. On load it matches values to parameters by id and skips ids it doesn't know. If the stored normalised value no longer round-trips to the stored plain value (the range changed), the plain value wins. Parameters missing from the chunk keep their current values.
- Extra state (anything that isn't a parameter) goes through `saveExtraState` and `loadExtraState`; the SDK cookbook recommends starting that blob with your own version byte and keeping defaults for versions you don't recognise. `loadExtraState` runs on the UI thread: stage the data and swap it in from `reset()`, which the framework calls on the audio thread after a load.
- Built-in programs (`addProgram(name, { values... })`) list plain values **in parameter order**: they are matched by index, extra values are ignored and missing ones are left alone. Generate these lists from id-keyed presets so they follow the spec's row order.
- For a plugin without chunk support, the MPC saves every parameter value of every program and restores them by writing each parameter back, which in VST 2.4 means by index: another reason indices must never shift. SDK plugins use chunks.

## Sources

All from the Akai MPC Plugin SDK, version 1.0 plus the "Unreleased (will become 1.1)" changes listed in `docs/changelog.md` (checked at commit e78bad5, 2026-11-23). MIT licence, copyright (c) 2026 inMusic Brands, Inc. Paraphrased; no long quotes.

- `docs/host-contract.md`: parameters, load sequence (parameter-0 nudge), MIDI, programs, state, MPC Sample.
- `docs/knob-fx.md`: the Knob FX mapping keys and rules, "Identity is permanent".
- `docs/presets.md`: built-in programs by index, `.xpl` files.
- `docs/dsp-cookbook.md`, sections 1 (rules 5, 6, 9, 10), 7 (parameter design for the MPC screen) and 8 (programs vs extra state).
- `framework/mpc_plugin.h`: `struct Param` (id, skew, automatable), the state chunk format in `internalSaveState` and `internalLoadState`, `setProgram`.
- `AGENTS.md`, "Hard rules": identity is permanent, effects get no MIDI, every effect ships a Knob FX mapping, parameter 0 is nudged.
