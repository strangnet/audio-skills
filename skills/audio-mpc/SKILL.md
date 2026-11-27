---
name: audio-mpc
description: Know-how for an Akai MPC plugin kept in the developer's own repository, outside the Akai MPC Plugin Builder SDK checkout, covering finding the SDK through `$MPC_SDK` or by asking, calling the SDK's build, validation, packaging and scaffolding tools and its host simulator from outside the checkout with absolute paths, where their output and tool cache go, the MPC's hard rules, keeping installs under the user's control, and reading Akai's `mpc-plugin-*` skills and SDK documents for facts while leaving their workflow out. Use when building, testing, validating, packaging or fixing an MPC plugin or MPC wrapper whose project sits outside an SDK checkout (for example next to a JUCE wrapper and a shared core); when running `build.py`, `validate.py` or `host_sim` on such a project, or one of them fails; or when the agent needs the SDK's location or an MPC fact from Akai's documents. Not for work inside an Akai MPC SDK checkout on a project in its `plugins/` folder, which Akai's own `mpc-plugin-*` skills cover (use those there). Not for a desktop-only plugin with no MPC target, and not for Claude Code or Cowork plugins.
---

# Audio MPC

An MPC plugin is built, validated and tested with Akai's MPC Plugin Builder SDK, a clone the user keeps somewhere on their machine. Akai's tools and skills assume the project sits in the SDK's `plugins/` folder and that the agent follows Akai's step order. This skill is for the other case: the MPC wrapper lives in the user's own repository, and the agent reaches into the SDK by absolute path, for its tools and for facts, while the user keeps their own process. Everything here is checked against the SDK at commit `e78bad5` (2026-11-23, changelog section "Unreleased (will become 1.1)"); the SDK has no release tags.

**Inside an SDK checkout, Akai's skills lead.** If the project sits under a folder that holds `tools/build.py` (an SDK checkout, usually in its `plugins/` folder), use Akai's `mpc-plugin-*` skills there and leave this skill aside.

## Finding the SDK

A folder is the SDK when it holds the SDK's build tool, `tools/build.py`. Call that folder `<sdk>` below.

- **`$MPC_SDK` names a folder that holds `tools/build.py`:** use it as `<sdk>`.
- **`$MPC_SDK` is unset, or its folder has no `tools/build.py`:** ask the user where their SDK clone is. A folder without the build tool isn't the SDK, whatever it's called.
- **The user names a folder:** check that `<folder>/tools/build.py` exists before using it. If it doesn't, say so and ask again.
- **Never search the disk** for the SDK (no `find`, `mdfind`, `locate` or `fd` over home or system folders), and **never clone it** without the user's yes.

Resolve `<sdk>` to an absolute path once, and use that path in every command.

## Calling the SDK's tools from outside

- **Call each tool by its absolute path inside `<sdk>`, and pass the project folder as an absolute path.** The build, validation and packaging tools take the project folder (the one holding `plugin.json` and `src/`) as a positional argument. Only the scaffolding tool, `new_plugin.py`, takes a folder through `--dir`, and that folder is the *parent* the new project is created in. Its default is `<sdk>/plugins`, so never run it without `--dir`, and run it only when the user asks for a new project.
- **Use `python3`** on macOS: the SDK's commands say `python`, which may not exist there.
- **Output goes into the project:** the build writes `<project>/build/` (the native library in `build/native/`, `params.json`, and the finished `<Manufacturer> - VST - <Name>/` folder), and packaging writes the zip to `<project>/dist/`. Keep `build/` and `dist/` out of version control, as the SDK's own `.gitignore` does.
- **The tool cache stays in the SDK:** `<sdk>/.sdk-tools/` holds the host simulator (`host_sim`) the build compiles, and zig when the build installs it there.
- **Test with the host simulator from the SDK's tool cache, on the native build:** `<sdk>/.sdk-tools/host_sim <project>/build/native/<slug>.dylib test`. Exit 0 is a pass (warnings allowed), 1 means at least one `FAIL`, 2 means the plugin crashed. Any `FAIL` line is a failed check.
- **Never copy between project and SDK.** Don't copy SDK files (framework headers, tools, templates) into the project: the build tool puts `<sdk>/framework` on the include path itself. Don't move the project into the SDK, and don't write the project's files into the SDK.
- **Translate relative SDK paths.** The build's closing packaging hint (`tools/package.py`) and Akai's skills (`.sdk-tools/host_sim`, `python tools/build.py plugins/<Name>`) are relative to the SDK; turn them into absolute paths before running them.

Every tool's exact arguments, outputs and exit codes: [references/sdk-tools.md](references/sdk-tools.md).

## Reading Akai's skills and documents

When the SDK is found and a task needs detail on a topic, read the SDK's own document or Akai's skill for it from `<sdk>`, by absolute path, for example `<sdk>/docs/host-contract.md` or `<sdk>/.agents/skills/mpc-plugin-test/SKILL.md`. Akai's skills sit in both `<sdk>/.claude/skills/` and `<sdk>/.agents/skills/` (identical copies). They aren't installed in the agent when the project lives outside the SDK, so read them as files.

From Akai's skills and the SDK's agent instructions (`AGENTS.md`), **keep the facts and hard rules, and leave out the workflow**:
- keep: what a finished plugin is, naming and identity rules, host behaviour, tool arguments and outputs, report meanings, error causes and fixes, the realtime and CPU rules, and the install-consent and no-system-modification rules
- leave out: the numbered step order, "scaffold a new project first", and every path that assumes the project is `<sdk>/plugins/<Name>`. Map `plugins/<Name>` to the user's project folder instead.

Which document holds which topic, and how to tell a fact from a workflow step: [references/reading-akai.md](references/reading-akai.md).

## References

Read only what the task needs:

- [references/sdk-tools.md](references/sdk-tools.md): the build, validation, packaging and scaffolding tools and the host simulator, called from outside the checkout: arguments, outputs, caches and exit codes.
- [references/reading-akai.md](references/reading-akai.md): the topic-to-document table, and what to keep and leave out when reading Akai's skills and `AGENTS.md`.

## Sources

Akai's MPC Plugin Builder SDK at commit `e78bad5` (inMusic Brands, MIT): `tools/build.py`, `tools/validate.py`, `tools/package.py`, `tools/new_plugin.py` (each tool's usage text and argument parser), `tools/host-sim/README.md` and `host_sim.cpp`, `AGENTS.md` ("Skills", "The workflow, every time", "Where to read"), and `.claude/skills/` and `.agents/skills/`. Paraphrased; each reference names the exact source of its facts.
