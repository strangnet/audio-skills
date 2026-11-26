# Parameter spec format

A parameter spec is one Markdown table that describes every parameter of a plugin, for both targets. It is the single place where ids, order, ranges and MPC labels are written down, so the core, the JUCE wrapper, the MPC wrapper, presets and the Knob FX mapping can all be checked against it.

Adapted from the Plugin Freedom System's parameter-spec templates (see Sources). The changes: one table instead of one section per parameter, an MPC label column, an automatable column, a smoothing column, and a fixed row order that doubles as the parameter order.

## The table

One row per parameter, in fixed order. Columns, in this order:

| Column | What goes in it |
|---|---|
| **id** | The stable id: lowercase ASCII, digits and `_`, short (`tilt`, `out_gain`, `hp_freq`). Never changes and is never reused once released. |
| **name** | The display name hosts show. Free to change at any time. |
| **MPC label** | 8 characters or fewer. Used where the MPC has little room, such as a Knob FX knob label. |
| **type** | `float`, `choice` or `bool`. |
| **range** | Plain values with their bounds (`-6 .. +6`), or the choice list in order (`LP, BP, HP`), or `off/on`. |
| **default** | A plain value inside the range, or the choice name. |
| **skew** | The curve from normalised 0..1 to the range: `linear`, `log`, or a skew factor with what it favours (`0.4, more resolution near 0`). `-` for choice and bool. |
| **unit** | `dB`, `Hz`, `ms`, `%`, `st`, `ct`, or `-`. |
| **automatable** | `yes` or `no`. |
| **smoothing** | Smoothing time for an audible change (`20 ms`), or `none` with the reason (a choice that crossfades, a non-automatable setting). |
| **notes** | Anything else that matters: why the default, which Knob FX knob, "retired in 1.3, inert", a dependency on another parameter. |

Rules:

- **Row order is the parameter order on both targets.** Row 0 is parameter index 0 in the JUCE wrapper and in the MPC wrapper.
- **Row 0 must be harmless.** The MPC host nudges parameter 0 on every prepare, so row 0 is a control whose brief jump is inaudible or harmless and has no side effects (an output trim). Never a trigger, reset, panic, bypass or mode switch.
- **New rows go at the bottom.** A released row is never moved or deleted. A removed parameter stays as a row marked retired in notes (and, for the MPC, stays in the list as an inert slot).
- Ids are unique across the whole history of the table, including retired rows.
- The type and range describe plain (real) values. Hosts see normalised 0..1; the skew column says how one maps to the other.

## Example

A tilt EQ effect, two releases in.

| id | name | MPC label | type | range | default | skew | unit | automatable | smoothing | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `out_gain` | Output | Output | float | -12 .. +12 | 0 | linear | dB | yes | 20 ms | Row 0: harmless when nudged. |
| `tilt` | Tilt | Tilt | float | -6 .. +6 | 0 | linear | dB | yes | 20 ms | Knob FX knob 1. |
| `pivot` | Pivot | Pivot | float | 200 .. 5000 | 1000 | log | Hz | yes | 20 ms | Knob FX knob 2. |
| `mix` | Mix | Mix | float | 0 .. 100 | 100 | linear | % | yes | 20 ms | Added in 1.1. Knob FX knob 3. |
| `quality` | Quality | Quality | choice | Eco, High | High | - | - | no | none: changes filter design, not automatable | Added in 1.1. |

## Checking work against the spec

- Every id in code (core, both wrappers) appears in the table, and every row appears in code, in the same order.
- Each MPC built-in program and each preset sets values by id, and covers every row (or relies on the documented default).
- The MPC effect's `knobs` and `shiftKnobs` indices point at the rows named in notes.
- Compare the table with the last released one: any changed id, moved row, deleted row, narrowed range or changed skew is a breaking change (see `state-and-migration.md`).

## Sources

- Plugin Freedom System, `.claude/skills/ui-mockup/assets/parameter-spec-template.md` and `.claude/skills/plugin-ideation/assets/parameter-spec-draft-template.md` (commit e965cdd, 2025-11-19), by TÂCHES (glittercowboy), MIT licence. Adapted, not copied: the type, range, default and skew fields come from there.
- Akai MPC Plugin SDK (1.0, with the unreleased 1.1 Knob FX changes; commit e78bad5), `docs/host-contract.md` for the parameter-0 nudge and `docs/knob-fx.md` for knob label length. MIT, copyright inMusic Brands, Inc.
