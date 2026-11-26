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

## Sandbox notes

- The agent runs with an isolated home directory, so toolchains installed under `~` are not visible, and package downloads are blocked. Cases use small scaffolded source trees and no toolchains.
- Case `env` keys must start with `EVAL_`, so `$MPC_SDK` can't be passed through. MPC cases use a stand-in scaffold that mimics an SDK checkout's layout without any SDK files.
