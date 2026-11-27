# Reading Akai's skills and documents for facts

The SDK carries its own documents in `<sdk>/docs/`, agent instructions in `<sdk>/AGENTS.md` (and `<sdk>/CLAUDE.md`), and nine `mpc-plugin-*` skills, as identical copies in `<sdk>/.claude/skills/` and `<sdk>/.agents/skills/`. When the project lives outside the SDK, the agent doesn't have those skills installed. Read them as files, by absolute path, when a topic needs detail.

Checked against the SDK at commit `e78bad5`. The table follows the "Where to read" and "Skills" tables in `AGENTS.md`.

## Where each topic lives

| Topic | SDK document | Akai's skill |
|---|---|---|
| How plugins work on the MPC | `<sdk>/docs/overview.md` | |
| Which MPCs, 32-bit and 64-bit, the MPC Sample | `<sdk>/docs/supported-devices.md` | |
| What the MPC host does (load sequence, parameters, MIDI, programs, state) | `<sdk>/docs/host-contract.md` | |
| The plugin folder, `plugin.json`, `version.xml`, `Content/` | `<sdk>/docs/plugin-folder-format.md` | |
| MPC Sample Knob FX, the 3 + 3 knob mapping | `<sdk>/docs/knob-fx.md` | |
| Writing DSP against the framework | `<sdk>/docs/dsp-cookbook.md`, `<sdk>/framework/mpc_plugin.h`, `<sdk>/framework/dsp/` | `mpc-plugin-dsp` |
| Touch UI: the simple `ui.json` | `<sdk>/docs/ui-guide.md`, `<sdk>/schemas/ui.schema.json` | `mpc-plugin-ui` |
| Touch UI: full skins (`TUI.json`, `Q-Links.json`) | `<sdk>/docs/ui-reference.md` | `mpc-plugin-ui` |
| Presets and built-in programs | `<sdk>/docs/presets.md` | `mpc-plugin-presets` |
| Building, toolchains and flags | `<sdk>/docs/building.md` | `mpc-plugin-build` |
| Testing with the host simulator | `<sdk>/docs/install-and-test.md`, `<sdk>/tools/host-sim/README.md` | `mpc-plugin-test` |
| Packaging a zip to share | | `mpc-plugin-package` |
| Installing on an MPC or MPC Sample | `<sdk>/docs/install-and-test.md`, `<sdk>/docs/knob-fx.md` | `mpc-plugin-deploy` |
| Problems on the MPC or with the tools | `<sdk>/docs/troubleshooting.md` | `mpc-plugin-troubleshoot` |
| Licences, JUCE, community | `<sdk>/docs/faq-and-legal.md` | |
| What changed since a version | `<sdk>/docs/changelog.md` | |

A skill's path is `<sdk>/.agents/skills/<skill>/SKILL.md` (or the same under `.claude/skills/`). `mpc-plugin-new` and `<sdk>/docs/workflow.md` describe Akai's whole process from idea to install: read them only for the facts they point to.

## What to keep and what to leave out

Akai's material mixes two things: facts about the MPC and the tools, and a workflow for a beginner working inside the SDK. Keep the first, and leave the second to the user, whose project already has its own process.

**Keep (facts and hard rules):**
- what a finished plugin folder holds, and how the tools build and check it
- naming and identity rules: names that must agree, the plugin id, parameter ids and order
- what the host does: the load sequence, the parameter 0 nudge, no MIDI to effects, block sizes, the MPC Sample
- the realtime and CPU rules, and "nothing proprietary"
- the meaning of a report line or an error, and its fix
- the install-consent and no-system-modification rules: they are safety rules, not workflow

**Leave out (workflow):**
- the numbered step order (`AGENTS.md` "The workflow, every time", `mpc-plugin-new`), and "never report done without steps 3 and 4" as a step list. What stays is the fact underneath: the build's validation and the host simulator must pass before a plugin is called done.
- "scaffold a new project first" with `new_plugin.py`. An existing project is never re-scaffolded, and a new one is scaffolded only when the user asks, with `--dir` outside the SDK.
- asking for the manufacturer name before anything else. That belongs to starting a new plugin; an existing project already names it in `plugin.json`.
- every path that assumes the project is `<sdk>/plugins/<Name>`. Akai writes `python tools/build.py plugins/<Name>` and `.sdk-tools/host_sim plugins/<Name>/build/native/...`; outside the SDK these become `python3 "<sdk>/tools/build.py" "<project>"` and `"<sdk>/.sdk-tools/host_sim" "<project>/build/native/..."`.
- style preferences for generated plugins (one `.cpp`, comment layout, number of programs). The user's project has its own conventions.

When a skill says "then run skill X" or "afterwards ASK ...", take the fact it carries (what X checks, what needs consent) and drop the sequencing.

## Sources

Akai's MPC Plugin Builder SDK at commit `e78bad5` (inMusic Brands, MIT), paraphrased:
- `AGENTS.md`: "Skills", "The workflow, every time", "Hard rules", "Where to read", "Style for generated plugins"
- `.claude/skills/` and `.agents/skills/`: the nine `mpc-plugin-*` skills (identical copies), especially `mpc-plugin-build` and `mpc-plugin-test` for the SDK-relative commands
- `docs/workflow.md`: the step-by-step process from idea to install
