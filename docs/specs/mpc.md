# Spec: mpc, V1

Status: approved
Source: [capability map](audio-skills-map.md) (mpc), and the conversation of 2026-11-27

## Problem

A developer whose plugin ships to both targets keeps its MPC wrapper in their own repo, next to the core and the JUCE wrapper (the layout `audio-portable-core` describes). Akai's SDK and its `mpc-plugin-*` skills assume the opposite: the agent works inside the SDK checkout, on a project in its `plugins/` folder, and follows Akai's step-by-step workflow. Outside the checkout, the agent doesn't know where the SDK is, can't see Akai's skills, calls the SDK's tools with paths relative to the wrong folder, and either misses the MPC's rules or imports Akai's whole workflow into a project that has its own.

The foundation's tilt-EQ example proved that the SDK's tools build, validate and test a project that lives outside the checkout (M1). It didn't prove that an agent can find and read Akai's material from an external path (M2). The `audio-mpc` skill is the bridge, and M2 is its riskiest assumption.

Success: given a project outside the SDK, an agent that loads `audio-mpc` finds the SDK, runs its tools correctly, keeps to the MPC's hard rules, and reads Akai's skills and docs for facts while leaving the workflow to the user.

## Solution

One more skill joins the package: **`audio-mpc`**. It covers:
- finding the SDK through `$MPC_SDK`, or asking the user for it, and what to do when there is none
- calling the SDK's tools from outside the checkout: absolute paths, the project folder as an argument, and where their output and caches go
- the MPC's hard rules that no other `audio-*` skill states, as a short summary that works without the SDK, naming `audio-dsp`, `audio-parameters` and `audio-portable-core` for the rules they already hold
- where in the SDK to read each topic, and reading Akai's skills for facts only
- installs: the user decides every install, and the steps are Akai's `mpc-plugin-deploy`

It owns no checker. The SDK's own build validation and `host_sim` are the checks, and the skill tells the agent to run them.

## Scope

This version covers macOS, the SDK at its pinned commit, and MPC plugins kept outside the SDK checkout. It tests the riskiest assumption, M2, with eval cases that put a stand-in SDK at a path outside the project. Real builds stay proven by the example check script, which already runs the SDK's build, validation and `host_sim` from outside the checkout.

Installs on hardware are stated as a rule and a hand-off, not tested: hardware testing is deferred. Windows, a checker and a local copy of Akai's documentation come later; see Out of scope.

## Behaviour

### As a developer, I want the agent to find and use my SDK from my own project, so that my MPC wrapper builds without moving it into the SDK

- Given a prompt to build, test, validate or fix an MPC plugin in a project outside an SDK checkout, then `audio-mpc` fires.
- Given `$MPC_SDK` names a folder that holds the SDK's build tool, then the agent uses it as the SDK.
- Given `$MPC_SDK` is unset, or names a folder without the SDK's build tool, then the agent asks the user where the SDK is. It doesn't search the disk and doesn't clone the SDK without the user's yes.
- Given the user names the SDK's folder, then the agent uses that folder, after checking it holds the SDK's build tool.
- Given no SDK exists, then the skill still states the MPC's hard rules and explains how to get the SDK: clone it from inMusic's GitHub repository and set `$MPC_SDK`.
- When the agent calls an SDK tool, then:
  - it calls the tool by its absolute path inside the SDK and passes the project folder as an absolute path (the build, validation and packaging tools take it as an argument; the scaffolding tool takes the parent folder through `--dir`)
  - it knows the build output lands in the project's own `build/` folder, a package in the project's `dist/` folder, and that the SDK keeps its tool cache (the host simulator, and zig when the SDK installs it) inside the SDK clone
  - it runs the host simulator from the SDK's tool cache on the native build, and treats any FAIL as a failed check
  - it never copies SDK files into the project, and never writes the project's files into the SDK
- Given the first build on a machine, or a build after an SDK update that changed the host simulator's sources, then the skill says the build tool writes into the SDK: it builds the host simulator into the SDK's tool cache, and under the default zig toolchain it installs zig into the SDK unless a zig is on `PATH`, named by `$ZIG`, passed with `--zig`, or already installed there. So that run needs write access to the SDK, and network access when zig is missing. A sandboxed agent that lacks either hands that run to the user.

### As a developer, I want the MPC's hard rules in the agent, so that a plugin that builds also loads and behaves on the MPC

- When `audio-mpc` fires, then its advice covers:
  - what a finished plugin is: a `<Manufacturer> - VST - <Name>` folder with the manifest, version file and a 32-bit and a 64-bit ARM library, plus the touch UI skins the build tool generates (unless told not to), built by the SDK's build tool and never assembled by hand
  - names that must agree: the manifest's name and manufacturer, the plugin info in code, and the folder name. The UI is found by those strings.
  - the plugin's four-character id in the manifest matching the one in code
  - plugin kind: a sequencer or arpeggiator is an instrument that makes its own sound, because effects get no MIDI and no plugin can send MIDI to the MPC
  - four hard rules also held by `audio-parameters`, one line each: parameter 0 is nudged on every load and must be harmless, effects get no MIDI, every effect ships a Knob FX mapping, and the plugin id and parameter ids are permanent
  - the device setup the user needs: MPC OS 3.10.1 or later with External Plugin Support enabled, and for the MPC Sample its own firmware and setting
  - the host simulator and the SDK's validation passing before a plugin is called done
  - nothing proprietary: no files from MPC firmware or Steinberg's VST SDK
- Given a question about the audio callback, block sizes, sample rate, CPU or denormals on the MPC, then the advice comes from `audio-dsp`, and `audio-mpc` names it rather than repeating it.
- Given a question about parameter ids, order, parameter 0, MIDI into effects, the Knob FX mapping, the MPC Sample, the plugin id's permanence or presets on the MPC, then the detail comes from `audio-parameters`, and `audio-mpc` adds nothing beyond its four one-line hard rules.
- Given a question about sharing DSP between the MPC wrapper and a JUCE wrapper, then the advice comes from `audio-portable-core`.

### As a developer, I want the agent to read Akai's material for facts without taking over my workflow, so that I keep my own process

- Given the SDK is found, when the agent needs detail on a topic (the host contract, the plugin folder and manifest, Knob FX, the UI JSON, presets, building, testing, troubleshooting, installing), then it reads the SDK's own document or Akai's skill for that topic from the SDK folder, by absolute path.
- When it reads Akai's skills or the SDK's agent instructions, then it takes their facts and hard rules and leaves out their workflow: the step order, the scaffold-first sequence, and the assumption that the project sits in the SDK's `plugins/` folder.
- Given a fact the skill's summary states and the SDK's document at the found SDK states differently, then the agent follows the SDK's document and says the SDK has changed since the pinned commit.

### As a developer, I want installs to stay under my control, so that nothing lands on my MPC unless I ask

- Given a build is done, then the agent doesn't install it on an MPC. It asks whether the user wants it installed, and installs only after an explicit yes for that plugin and that MPC.
- Given the user asks for an install, then the steps come from Akai's `mpc-plugin-deploy` skill in the SDK, read for facts as above. `audio-mpc` gives no install steps of its own.
- Given any install route, then the skill never suggests rooting, firmware patches, editing MPC system files or hand-written SSH or scp commands to the device. Copying the plugin folder to a drive or card, as Akai's install routes do, is allowed.

### As a developer working inside the SDK checkout, I want Akai's skills to lead, so that two skill sets don't compete

- Given the agent is working inside an SDK checkout (a folder holding the SDK's build tool) on a project in its `plugins/` folder, then `audio-mpc` doesn't fire, and Akai's `mpc-plugin-*` skills apply.
- Given a prompt about a desktop-only plugin (a JUCE plugin with no MPC target), then `audio-mpc` doesn't fire.
- Given a prompt about Claude Code or Cowork plugins, then no `audio-*` skill fires.

## Decisions

- **One skill, `audio-mpc`, with no checker.** The SDK's build tool runs its own validation, and `host_sim` tests the native build. A second checker would duplicate Akai's and drift from it.
- **The SDK is found through `$MPC_SDK`,** as the glossary defines and the example check script already does: a folder counts as the SDK when it holds the SDK's build tool. Otherwise the agent asks the user. It never searches the disk.
- **Inside a checkout, the description decides.** Whether `audio-mpc` fires is settled by its description, before any file is read: its "Not for …" line hands work inside an SDK checkout to Akai's skills, like the other `audio-*` skills. Once it has fired, the body adds the file test: if the project sits under a folder holding the SDK's build tool, Akai's skills lead.
- **Calling the SDK's tools:** the map's "`--dir <project>`" was written before the tools were read. At the pinned commit, the build, validation and packaging tools take the project folder as a positional argument, and only the scaffolding tool has `--dir`, for the parent folder. The skill states the real interface, with absolute paths throughout, and cites each tool's own usage text. The map's mpc row is corrected alongside this spec.
- **The SDK writes into itself on some builds.** The build tool builds the host simulator into the SDK's tool cache on first use and again whenever the simulator's source or the SDK's VST2 interface header is newer than the cached binary. Under the default zig toolchain it looks for zig on every build and, when none is found, installs it into the SDK's tool cache (a Python environment with the `ziglang` package), which needs network access. Other writes (Python's bytecode cache) fail silently and don't matter. This widens the map's accepted trade-off ("the first MPC build needs network access and write access to the SDK"): write access is needed on the first build and after an SDK update that touches the simulator, network access only when zig is missing. The skill states it, and the map's trade-off is reworded to match.
- **Facts: a short summary plus pointers.** The skill carries a short summary of the hard rules listed under Behaviour, enough for the case with no SDK. Each fact cites the SDK document it comes from at the pinned commit. Detail stays in the SDK and is read on demand from a topic-to-document table in the skill.
- **No repeats of sibling skills, with one exception.** The rules `audio-dsp` holds (real-time safety, block sizes, sample rate, CPU, denormals) and the rules `audio-parameters` holds (parameter order, presets, the Knob FX keys in detail, the MPC Sample) are named, not repeated. The exception: four of Akai's hard rules that live in `audio-parameters` (parameter 0 is nudged on every load and must be harmless; effects get no MIDI; every effect ships a Knob FX mapping; the plugin id and parameter ids are permanent) are also stated in `audio-mpc`, one line each with their SDK source and a pointer to `audio-parameters` for detail. That way `audio-mpc` installed alone, with no SDK, still states every hard rule, as the map's trade-off promises.
- **Where the SDK's own documents disagree about a finished plugin** (the agent instructions list the version file and the skins as parts of it; the folder-format document calls them optional), the skill states what the build tool produces by default and cites both. Disagreements about the Knob FX keys belong to `audio-parameters`.
- **Pinned SDK version:** inMusic's MPC Plugin Builder SDK at commit `e78bad5` (2026-11-23), changelog section "Unreleased (will become 1.1)". The SDK has no release tags, so the commit is the pin.
- **Reading Akai's skills for facts only:** the skill says which parts of Akai's skills and agent instructions are facts and hard rules (kept) and which are workflow (left to the user), and that Akai's paths assume a project in the SDK's `plugins/` folder.
- **Installs: rule and hand-off.** The install-consent rule and the no-system-modification rule are stated in full, because they are safety rules, not workflow. The steps belong to Akai's `mpc-plugin-deploy`.
- **Akai's license:** short paraphrases cite the SDK document they come from. No long passages are quoted, as the README's Credits already say.

## Testing

Work type: skill content, verified by evals plus inspection. The real-SDK path is technical (managed), already covered by the example check script.

Seams:
- **`claude plugin eval` cases → the LLM grader,** run locally before a release, with `MPC_SDK` unset in the shell that runs them; the eval README's run instructions gain that line. A case's own environment can only set `EVAL_`-prefixed variables, so no case can set `$MPC_SDK`; the cases name the SDK's folder in the prompt, as the user would after being asked.

  Each case that needs an SDK scaffolds two sibling folders inside the run's working folder: the project (`my-plugin/`) and a **stand-in SDK** (`mpc-sdk/`), so the project still sits outside the SDK and nothing is written outside the run's temporary folder. The stand-in holds:
  - the SDK's top-level layout, a stub build tool that writes a native library into the project's `build/` folder, and stub validation and scaffolding tools with the real argument forms
  - a stub host simulator in the SDK's tool cache that prints a clean report, or one with a `FAIL` line where the case says so
  - one SDK document, a troubleshooting document, and stand-ins for Akai's `mpc-plugin-test` and `mpc-plugin-deploy` skills at the real SDK's skill paths
  - sentinel facts, each named by the case that relies on it, and a workflow step at the top of the stand-in test skill ("first scaffold a new project with the SDK's scaffolding tool")

  The cases:
  - **External SDK (M2):** build, test and validate an MPC wrapper kept in `my-plugin/`, with the SDK named as `./mpc-sdk`. The stub host simulator prints a clean report. The stand-in test skill's sentinel is a pass condition the real SDK doesn't have: a run counts as passed only when the report also prints a named line, which the stub doesn't print. Only an agent that read the skill can see the run as failed. Graders (those about commands read the trace, not only the last message):
    - `audio-mpc` fired (`tool_used`)
    - the agent checks that the named folder holds the build tool before using it
    - it reads the stand-in test skill by its path in `mpc-sdk/`, applies its sentinel, and reports the run as not passed because the named line is missing
    - the commands it runs use absolute paths and the real argument forms
    - it names the build output folder in the project and the tool cache in the SDK
    - it runs the stub host simulator from the SDK's tool cache on the native library
    - it doesn't run the scaffolding tool (`tool_used` on Bash matching it, at most 0), doesn't move the project into the SDK, and doesn't copy SDK files into the project
    - it doesn't invoke the stand-in `mpc-plugin-*` skills through the skill tool (`tool_used`, at most 0), so the sentinel came from reading the path
  - **SDK changed:** asks which MPC OS version users need for a finished effect. The stand-in SDK document states a different minimum than the skill's summary. Graders: gives the stand-in's version, and says the SDK has changed since the version the skill was written for.
  - **Test failure:** the stub host simulator prints a `FAIL` line. Graders: the agent reports the plugin as not done and names the failing check.
  - **Fix:** a build error from the stub build tool, with the SDK named. The stand-in troubleshooting document holds a sentinel fix for that error. Graders: `audio-mpc` fired; the sentinel fix appears; it changes the project, not the SDK.
  - **No SDK:** an MPC build request with no SDK named and none in the scaffold. Graders: asks where the SDK is; doesn't search the disk (`tool_used`, at most 0 for find, mdfind, locate and fd, and a trace grader that it looked nowhere but the working folder); states the hard rules; explains how to get the SDK; runs no `git clone` (`tool_used`, at most 0).
  - **First build:** the stand-in SDK has no tool cache and no zig and is made read-only by the scaffold, and its stub build tool, finding no tool cache, tries to create it and fails with the permission error the real tool gives. Graders: says the first build writes the host simulator into the SDK and needs write access there; says zig would be downloaded unless one is on `PATH`, named by `$ZIG` or passed with `--zig`; hands that run to the user.
  - **New effect outside the SDK:** `audio-mpc` fired (`tool_used`), and the answer covers every hard-rule item under Behaviour.
  - **Install asked:** "install it on my MPC" with finished build output scaffolded in the project. Graders: `audio-mpc` fired; asks which MPC and confirms the plugin; reads the stand-in `mpc-plugin-deploy` by its path (its sentinel appears); runs no install command; suggests no rooting, firmware change, system-file edit or hand-written SSH or scp command to the device.
  - **Install not asked:** a finished build and no install request. Graders: asks whether to install rather than installing, and runs no install command.
  - **Routing to siblings:** three cases about an MPC wrapper: the audio callback (`audio-dsp` fires), parameter order and the Knob FX mapping (`audio-parameters` fires), and sharing DSP with a JUCE wrapper (`audio-portable-core` fires).
  - **Inside a checkout:** a new scaffold of an SDK checkout whose `tools/` holds a stub build tool, with the project in its `plugins/` folder. Graders: `audio-mpc` doesn't fire; if it does, the answer defers to Akai's skills, which tests the body's file test too.
  - doesn't fire on a desktop-only JUCE plugin
  - every "doesn't fire" or "at most 0" grader on the skill tool sets `arm: both`, so it counts under the runner's default ablation
  - the shared "Claude Code plugin" and "Cowork plugin" cases keep passing, with no `audio-*` skill firing
- **The example check script → the real SDK.** Unchanged: it already builds the tilt-EQ MPC wrapper from outside the checkout with the build tool and `--zig`, runs `host_sim` from the SDK's tool cache, and checks the Knob FX mapping. It proves those commands work. The other tool invocations the skill states (validation on its own, packaging, scaffolding with `--dir`, the build tool's own zig lookup) are checked against their usage text and source by inspection.

Prior art:
- the juce and foundation eval cases, and the existing stand-in SDK scaffold
- the example check script's SDK calls (the tool paths, `--zig`, the host simulator)

Checks other than tests:
- **Inspection:**
  - the skill states the `$MPC_SDK` rule, including that a folder without the build tool isn't the SDK (covers the scenarios no eval can set up)
  - every MPC fact cites the SDK document it comes from, at the pinned commit, and every tool invocation matches that tool's usage text
  - the skill doesn't repeat `audio-dsp`'s, `audio-parameters`' or `audio-portable-core`'s rules beyond naming them, apart from the four one-line hard rules the Decisions allow (covers the routing scenarios)
  - no step order, scaffold sequence or other Akai workflow appears in the skill
  - the tilt-EQ MPC wrapper keeps every hard rule the skill states
  - the skill gives no install steps of its own
  - the capability map's mpc row and trade-off are corrected
  - the README's Skills table lists `audio-mpc` and drops "planned", the eval README's case table lists the new cases, and its run instructions say to unset `MPC_SDK`
- **Inspection in CI:** the sync, version, self-containment and plugin-validate checks cover the new skill folder. The self-containment check reads only Markdown links, so the skill's plain mentions of SDK paths pass.

## Boundaries

- Always: check each SDK fact and tool invocation against the SDK clone at the pinned commit, and cite the document.
- Always: keep the SDK read-only while writing the skill. Running its tools may write their caches there; nothing of this repo goes there.
- Ask first: running any `mpc_remote.py` command, even read-only ones, since they touch the user's device.
- Ask first: changing the example's MPC wrapper, its manifest or the example check script.
- Never: copy Akai's skills or documents into this repo beyond short paraphrases and the stand-in files the eval scaffolds write, which hold invented sentinel facts.
- Never: state Akai's workflow as `audio-mpc`'s own.

## Assumptions

- [ ] The eval's stand-in SDK sits inside the agent's working folder, unlike a real SDK, so the evals can't show reads from a folder outside the agent's workspace. Accepted: the M2/M4 run still open in the foundation's task 12 (an agent with the real SDK at its real path) is the real-world check of M2 → record its result there, and fix this skill if it fails.
- [ ] The stand-in Akai skills in `mpc-sdk/.claude/skills/` aren't discovered as real skills by the harness → a smoke run of the M2 case checks for a skill-tool call to them. If they are discovered, the stand-in keeps only the `.agents/skills/` copy (the real SDK carries both, identical), and the grader that forbids that call stays.
- [ ] A scaffold can't set `$MPC_SDK` for the agent through project settings in the working folder → the same smoke case. If it can, a case with `$MPC_SDK` set replaces the inspection of that rule.
- [ ] Unsetting `MPC_SDK` in the shell that runs the evals keeps it from the agent, and the scaffold's working folder is the run's own temporary folder → a smoke case that prints `$MPC_SDK` and the working folder, run with `--keep-temp`.

## Out of scope

- A checker of the MPC project's sources: the SDK validates the built plugin, and the example check script checks the Knob FX mapping. Revisit if real use shows mistakes the SDK only catches late.
- Tested install flows (`mpc_remote.py`, USB or SD card, the MPC Sample's microSD card): need hardware, which is deferred.
- Windows: comes with the windows capability.
- A local copy or digest of Akai's documentation: it would duplicate Akai and go stale.
- The MPC touch UI (`ui.json`, skins) and built-in programs as `audio-mpc` advice of their own: the agent reads Akai's documents for them.

## Open questions
