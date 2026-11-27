---
name: audio-mpc
description: Know-how for an Akai MPC plugin kept in the developer's own repository, outside the Akai MPC Plugin Builder SDK checkout, covering finding the SDK through `$MPC_SDK` or by asking, calling the SDK's build, validation, packaging and scaffolding tools and its host simulator from outside the checkout with absolute paths, where their output and tool cache go, the MPC's hard rules, keeping installs under the user's control, and reading Akai's `mpc-plugin-*` skills and SDK documents for facts while leaving their workflow out. Use when starting, writing, building, testing, validating, packaging or fixing an MPC plugin or MPC wrapper whose project sits outside an SDK checkout (for example next to a JUCE wrapper and a shared core); when running `build.py`, `validate.py` or `host_sim` on such a project, or one of them fails; or when the agent needs the SDK's location or an MPC fact from Akai's documents. Not for work inside an Akai MPC SDK checkout on a project in its `plugins/` folder, which Akai's own `mpc-plugin-*` skills cover (use those there). Not for a desktop-only plugin with no MPC target, and not for Claude Code or Cowork plugins.
---

# Audio MPC

An MPC plugin is built, validated and tested with Akai's MPC Plugin Builder SDK, a clone the user keeps somewhere on their machine. Akai's tools and skills assume the project sits in the SDK's `plugins/` folder and that the agent follows Akai's step order. This skill is for the other case: the MPC wrapper lives in the user's own repository, and the agent reaches into the SDK by absolute path, for its tools and for facts, while the user keeps their own process. Everything here is checked against the SDK at commit `e78bad5` (2026-11-23, changelog section "Unreleased (will become 1.1)"); the SDK has no release tags.

**Inside an SDK checkout, Akai's skills lead.** If the project sits under a folder that holds `tools/build.py` (an SDK checkout, usually in its `plugins/` folder), use Akai's `mpc-plugin-*` skills there and leave this skill aside.

## The MPC's hard rules

These hold with or without the SDK at hand. Each rule's source and detail: [references/hard-rules.md](references/hard-rules.md).

- **A finished plugin** is a `<Manufacturer> - VST - <Name>/` folder holding `plugin.json`, `version.xml`, a 32-bit and a 64-bit ARM library (`VST/<slug>-arm32.so`, `VST/<slug>-arm64.so`) and the touch UI skins (`Plugin Skins/`) the build tool generates unless told `--no-ui`. The SDK's build tool makes it; never assemble or patch it by hand.
- **Names agree:** `plugin.json`'s `name` and `manufacturer`, `PluginInfo`'s `name` and `vendor` in code, and the two parts of the folder name are the same strings. The MPC finds the UI by them.
- **One four-character id:** `plugin.json`'s `uid` (such as `"AcWb"`) matches `PluginInfo::uniqueId = MPC_FOURCC('A','c','W','b')` in code.
- **Plugin kind:** effects get no MIDI and no plugin can send MIDI to the MPC, so a sequencer or arpeggiator is an instrument that makes its own sound.
- Four rules the `audio-parameters` skill holds in detail, one line each:
  - parameter 0 is nudged on every load and must be harmless (`docs/host-contract.md`)
  - effects get no MIDI (`docs/host-contract.md`)
  - every effect ships a Knob FX mapping in `plugin.json` (`AGENTS.md`, `docs/knob-fx.md`)
  - the plugin id and parameter ids (and their order) are permanent (`AGENTS.md`, `docs/knob-fx.md`)
- **Device setup to tell the user:** MPC OS 3.10.1 or later with External Plugin Support enabled (Preferences → Enhancements (Beta)); for an effect on the MPC Sample, firmware v1.4.0 or later with Custom Plug-In Support enabled (MIDI Config → Dev Enhancements (Beta)). Instruments don't run on the MPC Sample.
- **Done means passing:** the SDK's validation reports no errors and the host simulator's test has no `FAIL` line. Until both hold, the plugin isn't done.
- **Nothing proprietary:** no files from MPC firmware or Steinberg's VST SDK.

For the audio callback, block sizes, sample rate, CPU and denormals, use the `audio-dsp` skill. For parameter design, order, presets, the Knob FX keys and the MPC Sample, use `audio-parameters`. For sharing DSP with a JUCE wrapper, use `audio-portable-core`.

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

## No SDK

When the user has no SDK clone, or none is found and they don't name one, nothing can be built, validated or tested. Say so, and still give the MPC's hard rules this skill summarises: they hold with or without the SDK. Then say how to get the SDK:
- clone inMusic's repository, `https://github.com/inmusic-software/mpc-plugin-builder-sdk`, to a folder outside the project (it needs Python 3.9 or later)
- set `MPC_SDK` to the clone's absolute path in the shell profile, for example `export MPC_SDK="$HOME/code/mpc-plugin-builder-sdk"`

Clone it only after the user says yes. The first build afterwards writes into the clone (next section).

## Builds that write into the SDK

Most builds only write into the project, but some write into `<sdk>/.sdk-tools/`:
- **The host simulator:** the build compiles `host_sim` there when it's missing (the first build with this clone) or older than `tools/host-sim/host_sim.cpp` or `framework/mpc_vst2_abi.h` (after an SDK update that touched them). This needs write access to the SDK, whatever the toolchain.
- **zig:** under the default zig toolchain, every build looks for zig in `--zig`, `$ZIG`, `PATH` and `<sdk>/.sdk-tools/zigenv`. When none works, it installs the `ziglang` package into that `zigenv`, which needs write access and network access. Passing `--zig` or setting `ZIG` to a zig the user already has avoids the install.

If the agent can't write to the SDK or reach the network (a sandbox, a read-only clone), **hand that run to the user**: give the exact build command with absolute paths, say what it will write and where, and why it needs the access. Don't work around it: no `chmod` or `sudo` on the SDK, no copy of the SDK, no host simulator built elsewhere, no edit to the build tool. Later builds write nothing there until the SDK changes again.

What a failed write looks like, and the zig lookup in detail: [references/sdk-edge-cases.md](references/sdk-edge-cases.md).

## Failures, fixes and a changed SDK

- **A host simulator `FAIL` is a failed check,** as are a crash (exit 2), a validation `ERROR` and a failed build. The plugin isn't done: say which check failed, quoting the `FAIL` line and its section, even when everything else passed.
- **A fix changes the project, not the SDK.** Even when the error points into an SDK file (a framework header, a tool), the fix goes in the project's sources, `plugin.json` or `ui.json`. Look the error up in `<sdk>/docs/troubleshooting.md` and Akai's `mpc-plugin-troubleshoot` skill. Never edit, patch or replace SDK files; if the SDK itself looks wrong, tell the user.
- **The SDK's document wins.** When a fact in this skill differs from the found SDK's document, follow the document, and tell the user the SDK has changed since commit `e78bad5`, the one this skill was checked against. Name the document and both values. For example, if the SDK names a newer minimum MPC OS than the device setup above, give the SDK's.

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
- [references/sdk-edge-cases.md](references/sdk-edge-cases.md): getting the SDK, builds that write into it (when, what a failed write looks like, the hand-off), failures and fixes, and a changed SDK.
- [references/hard-rules.md](references/hard-rules.md): the MPC's hard rules in detail, with the SDK document each comes from, and where the SDK's own documents disagree about a finished plugin.

## Sources

Akai's MPC Plugin Builder SDK at commit `e78bad5` (inMusic Brands, MIT): `tools/build.py`, `tools/validate.py`, `tools/package.py`, `tools/new_plugin.py` (each tool's usage text and argument parser), `tools/host-sim/README.md` and `host_sim.cpp`, `AGENTS.md` ("Skills", "The workflow, every time", "Where to read"), and `.claude/skills/` and `.agents/skills/`. Getting the SDK, builds that write into it, fixes and device setup: `README.md` ("Requirements"), `docs/building.md` ("Toolchain: zig"), `docs/troubleshooting.md`, `docs/supported-devices.md` ("Side by side"), and `tools/build.py` (`find_zig`, `Builder.ensure_host_sim`, `main`). Paraphrased; each reference names the exact source of its facts.

The hard rules come from `AGENTS.md` ("What a finished plugin is", "Hard rules"), `docs/plugin-folder-format.md`, `docs/host-contract.md`, `docs/knob-fx.md`, `docs/supported-devices.md`, `docs/install-and-test.md`, `docs/faq-and-legal.md` and `framework/mpc_plugin.h` at the same commit; [references/hard-rules.md](references/hard-rules.md) cites each one.
