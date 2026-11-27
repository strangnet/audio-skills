# strangnet audio skills

Audio-plugin know-how for AI coding agents: real-time-safe DSP, parameter and state design, and sharing one DSP core between desktop plugins (JUCE 9: VST3, AU and CLAP) and Akai MPC plugins. The skills hold technical facts, rules and pitfalls only. They never prescribe a workflow, so they work alongside whatever process skills you already use, such as [strangnet-skills](https://github.com/strangnet/agent-skills).

## Install

There are two kinds of install. A **plugin** is a read-only bundle that updates when a new version is released. **[skills.sh](https://skills.sh)** (`npx skills`) copies the skill folders into your project or home directory, where you can edit them, and you update them yourself. Pick one per agent: installing both gives you every skill twice.

### Claude Code

```bash
claude plugin marketplace add strangnet/agent-skills
claude plugin install strangnet-audio-skills@strangnet
```

Or from inside a session: `/plugin marketplace add strangnet/agent-skills`, then `/plugin install strangnet-audio-skills@strangnet`. The `strangnet` marketplace also lists `strangnet-skills`. Run `claude plugin marketplace update strangnet` to pick up new releases.

### Codex

```bash
codex plugin marketplace add strangnet/audio-skills
codex plugin add strangnet-audio-skills@strangnet-audio-skills
```

Start a new Codex session afterwards so it discovers the skills. Mention a skill by name to invoke it, or describe the task and let Codex pick one.

### GitHub Copilot (CLI and VS Code)

```bash
copilot plugin marketplace add strangnet/agent-skills
copilot plugin install strangnet-audio-skills@strangnet
```

Run `copilot plugin update strangnet-audio-skills` to pull new releases. In VS Code, enable the `chat.plugins.enabled` setting, run **Chat: Install Plugin From Source** and enter `https://github.com/strangnet/audio-skills`.

### pi

```bash
pi install git:github.com/strangnet/audio-skills        # every project
pi install git:github.com/strangnet/audio-skills -l     # this project only, shareable via .pi/settings.json
```

pi finds every `SKILL.md` under `skills/` and registers each as a `/skill:<name>` command. Run `pi update --extensions` to pull new releases.

### Any other agent (skills.sh)

```bash
npx skills@latest add strangnet/audio-skills                        # choose skills and agents interactively
npx skills@latest add strangnet/audio-skills --skill audio-dsp      # one skill
npx skills@latest add strangnet/audio-skills --list                 # list skills without installing
```

Every skill works when installed on its own: each carries its own references and scripts. Add `-g` to install into your home directory instead of the project.

## Skills

| Skill | What it gives the agent |
|---|---|
| `audio-dsp` | Real-time rules for the audio callback and the code it calls, denormals, smoothing, aliasing and oversampling, latency, block sizes, the MPC's CPU budget, a DSP architecture checklist, and a real-time checker script. |
| `audio-parameters` | Parameter, state and preset design: stable ids, ranges and skew, automation, the MPC host's parameter rules and Knob FX mapping, and versioned state with migrations. |
| `audio-juce` | JUCE 9 plugins with CMake on macOS: finding JUCE, plugin codes, module headers, CLAP through clap-juce-extensions, bus layouts for effects and instruments, the parameter tree, threads, the editor's lifecycle, programs, and host-facing pitfalls such as stale bundles. |
| `audio-portable-core` | One DSP core behind both a JUCE plugin and an MPC plugin: header-only standard-library C++17, relative includes, no host types, parameters defined once, and a core-purity checker script. |

Inside an Akai MPC SDK checkout, Akai's own `mpc-plugin-*` skills cover MPC-only work, and these skills step aside. A skill for the MPC SDK (`audio-mpc`) is planned.

### Checkers

Two skills ship a checker: Python 3, standard library only, reading source code only. Run them from the skill's folder:

```bash
python3 scripts/check_realtime.py [--verbose] <file-or-folder>...   # audio-dsp
python3 scripts/check_core_purity.py <core folder>...               # audio-portable-core
```

Each prints `file:line: severity: rule: message` and exits 0 (no errors), 1 (errors) or 2 (usage error).

## Example

`examples/tilt-eq/` is a tilt EQ with one portable core, a JUCE wrapper (VST3, AU and CLAP, with a WebView UI) and an MPC wrapper. Its check script builds and validates everything:

```bash
JUCE_DIR=<JUCE 9.0.6> MPC_SDK=<Akai SDK clone> python3 examples/tilt-eq/check.py
```

It runs the real-time, core-purity and WebView binding checkers, the core's behaviour test, the JUCE build with pluginval, clap-validator and auval, and the MPC build for arm32 and arm64 with the SDK's validation and `host_sim`. A missing tool skips only the checks that need it. Nothing is installed, apart from copying the AU into `~/Library/Audio/Plug-Ins/Components` so auval can see it. The example doesn't ship inside any skill.

## Development

```bash
uv run pytest                              # repo tooling and checker tests
scripts/sync-references.sh --check         # vendored references match references/
uv run scripts/check_versions.py .         # all manifests share one version
uv run scripts/check_self_contained.py .   # no skill links outside its folder
claude plugin validate .                   # manifests and skills load
```

CI runs all five. Behavioural evals run locally with `claude plugin eval`; see [evals/plugin/README.md](evals/plugin/README.md). Specs live in `docs/specs/`, and agent rules in [CLAUDE.md](CLAUDE.md).

## Credits

- The real-time rules and the DSP architecture checklist build on the [Plugin Freedom System](https://github.com/glittercowboy/plugin-freedom-system) by Taches (glittercowboy), MIT as stated in its README: its DSP agent's real-time safety rules and its architecture template.
- The MPC facts are paraphrased from Akai's [MPC Plugin Builder SDK](https://github.com/inmusic-software/mpc-plugin-builder-sdk) by inMusic Brands, MIT (copyright (c) 2026 inMusic Brands, Inc.). Each reference cites the SDK document it draws on and the commit it was checked against. No long passages are quoted.

## License

MIT. See [LICENSE](LICENSE).
