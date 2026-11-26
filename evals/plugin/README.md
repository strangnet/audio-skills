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

## Sandbox notes

- The agent runs with an isolated home directory, so toolchains installed under `~` are not visible, and package downloads are blocked. Cases use small scaffolded source trees and no toolchains.
- Case `env` keys must start with `EVAL_`, so `$MPC_SDK` can't be passed through. MPC cases use a stand-in scaffold that mimics an SDK checkout's layout without any SDK files.
