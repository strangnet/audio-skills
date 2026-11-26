# Spec: foundation, V1

Status: approved
Source: conversation (shape session, 2026-11-26); [capability map](audio-skills-map.md)

## Problem

Patrick builds audio plugins with whichever AI agent he's using: Claude Code, Codex and others. Agents write plugin code that compiles but breaks real-time rules, chooses unstable parameter ids, and ties DSP to one framework, so the same idea can't ship both as a desktop plugin and on an MPC. The best know-how around is locked inside the Plugin Freedom System, which only works in Claude Code and also imposes its own workflow. Akai's SDK covers the MPC but knows nothing about desktop.

Success for this first version: one small plugin idea becomes a desktop plugin and an MPC plugin from **one unchanged core**, guided by skills that any agent can load, and nothing in the package dictates the order of work.

## Solution

The user installs `strangnet-audio-skills` into their agent next to their usual process skills. When they work on a plugin, the agent loads three skills as needed:

- **`audio-portable-core`**: how to write a core that both wrappers can use.
- **`audio-dsp`**: real-time-safe DSP know-how.
- **`audio-parameters`**: parameter, state and preset design for both targets.

Two checkers let the agent, or the user, prove that the core is pure and that the real-time code is safe. A tilt-EQ example in the repo shows a core and both wrappers working, and a local check script proves it end to end.

## Scope

This version is the **walking skeleton**: the repo structure, distribution, CI and eval setup that every later capability relies on. Alongside it come the three skills and two checkers the example needs. It comes first because it tests the four assumptions the whole package depends on:

- **M1**: one core builds unchanged behind both wrappers.
- **M2**: agents can read Akai's skills from an external path (exercised only by hand here; `audio-mpc` comes later).
- **M3**: clap-juce-extensions works on JUCE 9.0.6.
- **M4**: know-how-only skills plus the user's own workflow get from idea to a validated plugin.

The example's JUCE wrapper and MPC wrapper are written directly in this version, without the help of `audio-juce` or `audio-mpc`, because those skills come later. What's learned writing them feeds those specs.

## Behaviour

### As a plugin developer, I want to install the package into my agent, so that the audio skills are available wherever I work

- Given Claude Code with the `strangnet` marketplace added, when the user installs `strangnet-audio-skills@strangnet`, then the three `audio-*` skills are listed, and invoking one by name loads it.
- Given Copilot CLI, when the user installs it from the same marketplace, then the skills are available (the same Claude plugin manifests).
- Given Codex, when the user adds the plugin from this repo's Codex marketplace, then the three skills are available.
- Given pi or skills.sh, when the user installs from the git repo, then each skill folder is found on its own.
- Given one skill folder copied alone (skills.sh), when the agent loads it, then every file the skill refers to is inside that folder.
- Given this repo's manifests disagree on the version, when CI runs, then the version check fails.
- Given a shared reference file was edited only in a skill's copy and not at the root, when CI runs, then the sync check fails.
- Given `strangnet-skills` is installed too, when both are listed, then no skill names collide.

### As a developer building for both targets, I want the agent to know how to structure a portable core, so that one DSP implementation ships to desktop and MPC

- Given a prompt to share DSP between a JUCE plugin and an MPC plugin, when the agent picks skills, then `audio-portable-core` fires.
- When it fires, then its advice covers:
  - the core is header-only C++17 that uses only the standard library
  - each wrapper includes the core by a relative path from its own source folder (because the SDK build compiles and includes only the project's `src/`)
  - the core never sees host types: the wrapper converts host buffers, parameters and sample rate into plain types
  - the core's real-time entry points carry the real-time marker so the checker scans them
  - parameter ids and order are defined once in the core and reused by both wrappers
  - running the core-purity checker
- Given a desktop-only prompt (a JUCE reverb with no MPC), then `audio-portable-core` doesn't fire.
- Given a prompt to build a Claude Code plugin, then no `audio-*` skill fires.
- Given a prompt to build a Cowork plugin, then no `audio-*` skill fires.
- Given the agent is working inside an Akai SDK checkout on an MPC-only plugin, then `audio-portable-core` doesn't fire, because Akai's own skills cover that case.

### As a developer, I want real-time-safe DSP know-how in the agent, so that my audio callback doesn't glitch or crash hosts

- Given a prompt to write or review an audio callback (`processBlock`, or `process` in an MPC wrapper), then `audio-dsp` fires.
- When it fires, then its advice covers:
  - no allocation, locks, blocking I/O or logging in real-time code, including the core functions the callback calls
  - denormal protection
  - parameter smoothing
  - aliasing and when to oversample
  - latency reporting to the host
  - variable block sizes (the MPC delivers 32–512 frames per call; the announced size is only a maximum)
  - a CPU budget per target (the 32-bit MPC limits are the tightest)
  - running the real-time checker on the wrapper and on the core
- Given a prompt to plan a plugin's DSP, then `audio-dsp` offers its architecture checklist: signal chain, mono or stereo layout, latency, oversampling, sample-rate dependence (the MPC is fixed at 44.1 kHz) and CPU budget.
- Given the same prompt, then it offers no planning steps, no step order and no document templates.
- Given a prompt about offline audio-file processing with no plugin (a WAV batch converter), then `audio-dsp` doesn't fire.

### As a developer, I want parameter and state know-how in the agent, so that automation, presets and saved sessions keep working across targets and versions

- Given a prompt to add or change a parameter, preset or saved state, then `audio-parameters` fires.
- When it fires, then its advice covers:
  - parameter ids are stable forever and never reused
  - ranges, skew and units
  - which parameters can be automated, and how
  - the MPC constraints:
    - the parameter count is fixed at load
    - parameter 0 must be harmless because the host nudges it
    - the host ignores defaults, step counts and text-to-value
    - effects get no MIDI
    - every effect needs a Knob FX mapping
  - saved state carries a version and old versions still load
  - presets reference parameters by id, not by index
  - the parameter spec format defined under Decisions
- Given a request to remove or rename a parameter in a released plugin, then the advice says to keep the old id and migrate saved state rather than renumber.
- Given a prompt about Claude Code plugin settings or CLI parameters, then `audio-parameters` doesn't fire.

### As a developer or an agent, I want to check that a core is pure, so that it is proven to compile behind both wrappers

- Given a core folder whose headers include only standard-library headers and each other, when the core-purity checker runs, then it reports no findings and exits with success.
- Given a core header that includes a JUCE header, or uses a `juce::` name or a `JUCE_` macro, when it runs, then it reports each one with `file:line` and exits with failure. This applies even when no JUCE include is present.
- Given a core header that includes an SDK header, or uses an `mpc::` name, when it runs, then it reports each one with `file:line` and exits with failure.
- Given a core header that includes a non-standard third-party header, when it runs, then it reports it and exits with failure.
- Given a core folder with a `.cpp` file, when it runs, then it reports that the core must be header-only and exits with failure.
- Given `juce::` appears only inside a comment or a string literal, when it runs, then it doesn't report it.
- Given a core header that includes a deprecated C header such as `<math.h>`, when it runs, then it reports a `warning` naming the replacement (`<cmath>`), and warnings alone exit with success.
- Given a core folder that holds only source files, when it runs, then it reports each one as a header-only error rather than a usage error.
- Given a path that doesn't exist, or one with no headers or source files, when it runs, then it prints usage and exits with the usage-error code, distinct from the failure code.

### As a developer or an agent, I want to check that real-time code is safe, so that common glitch causes are caught before they reach a host

- Given a JUCE wrapper source whose `processBlock` body is clean, when the real-time checker runs, then it reports no findings and exits with success.
- Given a real-time body that contains any of the following, when it runs, then each one is reported with `file:line`, severity `error` and the rule it breaks, and it exits with failure:
  - allocation: `new`, `delete`, `malloc`, `free`, growing a standard container (`push_back`, `emplace_back`, `resize`, `reserve`, `insert`), or declaring a local standard container variable (`std::vector`, `std::string`, `std::deque`, `std::list`, `std::map`, `std::set`, `std::unordered_map`, `std::unordered_set`), such as `std::vector<float> gains(numFrames);`
  - a lock: `mutex`, `lock_guard`, `unique_lock`, `scoped_lock`
  - file or network I/O
  - logging or console output: `cout`, `cerr`, `printf`, `fprintf`, `DBG`, `Logger`, and the MPC SDK's `mpc::log`
- Given an MPC wrapper's `process(ProcessContext&)` body that breaks a rule, when it runs, then it reports it in the same way.
- Given a core function that carries the real-time marker and breaks a rule, when it runs on the core, then it reports it in the same way.
- Given a JUCE `processBlock` with no denormal protection, when it runs, then it reports a finding with severity `warning`. Warnings alone exit with success.
- Given an allocation outside every real-time body (in a constructor, or in prepare or reset), when it runs, then it doesn't report it.
- Given an in-class (inline) `processBlock` followed by a constructor that allocates, when it runs, then only the `processBlock` body is scanned.
- Given a forbidden word that appears only in a comment or a string literal inside a real-time body, when it runs, then it doesn't report it.
- Given a helper class with a method named `process` whose parameter isn't `ProcessContext`, when it runs, then that method isn't scanned unless it carries the real-time marker.
- Given a flagged line that carries the opt-out marker with a reason, when it runs, then it doesn't report that line, and verbose mode lists it with its reason.
- Given an opt-out marker with no reason, when it runs, then the marker itself is reported as an error.
- Given a source file with no real-time body, when it runs, then it says so and exits with success.
- Given a bad path, or a folder with no source files, when it runs, then it prints usage and exits with the usage-error code.

### As the package author, I want a tilt-EQ example built end to end, so that M1–M4 are proven on real toolchains

- Given JUCE 9.0.6, clap-juce-extensions at its pinned commit, zig, and the SDK found through `$MPC_SDK`, when the example check script runs on macOS, then:
  - the core passes the core-purity checker
  - the core and both wrappers pass the real-time checker
  - the core's behaviour test passes:
    - at 0 dB tilt, the output equals the input to within −90 dB
    - a positive tilt raises a 10 kHz sine and lowers a 100 Hz sine, and a negative tilt does the reverse
    - after a jump in the tilt parameter at 44.1 kHz, the smoothed tilt value moves monotonically to the target, gets within 1% of it between 15 ms and 25 ms after the jump, and never moves more than 1% of the jump in a single sample
  - the JUCE wrapper builds VST3, AU and CLAP
  - pluginval passes at strictness level 10 for VST3 and AU
  - clap-validator passes for the CLAP build
  - auval passes for the AU build
  - the MPC wrapper builds for arm32 and arm64 through the SDK's own build tool, including its validation step
  - the MPC manifest declares a Knob FX mapping
  - `host_sim` reports no FAIL
  - the script exits with success and prints a summary line for each check
- Given the source tree, then exactly one copy of each core header exists, both wrappers' include directives resolve to those files, and neither build modifies them.
- Given a required tool is missing (pluginval, clap-validator, the SDK, zig or JUCE), when the script runs, then it skips only the checks that need that tool, says what's missing and where to get it, and installs nothing. The script itself looks for zig before it calls the SDK's build tool, so the build tool never installs zig itself.
- Given any check fails, then the script still runs every check that doesn't depend on the failed one, and lists every failed and skipped check.
- Given the results of a run, then the overall outcome is **fail** if any check failed, otherwise **incomplete** if any check was skipped, otherwise **pass**. Each outcome has its own exit code. A check skipped because a check it depends on failed counts toward fail, not incomplete.
- Given the built plugin is loaded in a DAW, when the user moves the tilt control in the WebView UI, then the tilt parameter changes and is recorded as automation. This is a manual check.
- Given the MPC build is copied to an MPC, when the user loads it, then the tilt control appears on a Q-Link and changes the sound. This is a manual check.
- Given the MPC wrapper, then its parameter 0 is harmless (a nudge from the host makes no audible change), as Akai's rules require.

### As a reader of the repo, I want to know what's included and where it came from, so that I can install it and trust its sources

- Given the README, then it lists every skill with one line each, the install command for each agent, the CI and eval commands, and a Credits section that names the Plugin Freedom System by Taches (glittercowboy, MIT) and Akai's MPC Plugin Builder SDK (inMusic, MIT).
- Given any skill text that quotes Akai's material at length, then Akai's MIT notice goes with it. Short paraphrases cite the SDK document they come from.
- Given the repo's own license, then it is MIT, matching `agent-skills`.

## Decisions

- **Package and distribution:**
  - The plugin is named `strangnet-audio-skills`.
  - It's listed in the existing `strangnet` marketplace (in the `agent-skills` repo) as a GitHub source pointing at this repo.
  - This repo carries its own Claude plugin manifest, a Codex plugin manifest and a Codex marketplace, mirroring `agent-skills`.
  - These three manifests carry one version number. It starts at 0.1.0 and follows the same semver rules as `agent-skills`.
  - The `strangnet` marketplace entry carries **no version**, so this repo's plugin manifest is the only source of the version. This repo's version check covers its own three manifests and doesn't expect a Claude marketplace file here.
- **Repo layout mirrors `agent-skills`:** flat `skills/`, a root `references/` for shared sets copied into skills by a sync script, `evals/plugin/` in the `claude plugin eval` format, `scripts/` for repo tooling, and an `AGENTS.md` that is a symlink to `CLAUDE.md` and holds the authoring conventions. Adding the listing to the `strangnet` marketplace in `agent-skills` is a change to that repo.
- **A self-containment check** runs in CI. Every relative link or path that a skill's files mention must resolve inside that skill's folder.
- **Skill rules:**
  - Every skill is named `audio-*`.
  - Its description says what it does, "Use when …" with concrete triggers, and "Not for …" lines that hand off to Akai's `mpc-plugin-*` skills inside an SDK checkout and exclude agent-plugin topics (Claude Code and Cowork plugins).
  - Skills hold know-how only: no step order, no planning templates.
- **Parameter spec format** (taught by `audio-parameters`, adapted from the Plugin Freedom System's parameter-spec template): a table with one row per parameter, in fixed order. Columns:
  - stable id
  - display name
  - MPC label, 8 characters or fewer (the Q-Link and Knob FX label; the parameter name itself may be longer)
  - type: float, choice or bool
  - range
  - default
  - skew or curve
  - unit
  - automatable: yes or no
  - smoothing time
  - notes

  The row order is the parameter order on both targets, and row 0 must be harmless. Presets are keyed by id; where a target matches by index (MPC built-in programs, the Knob FX mapping), those lists are generated from the id-keyed presets in row order, and rows are never reordered.
- **Shared checker interface:**
  - Python 3, standard library only, reading source code only.
  - The checkers live in the skill that owns them: the core-purity checker in `audio-portable-core`, the real-time checker in `audio-dsp`.
  - They take one or more file or folder paths. Headers are `.h` and `.hpp`; sources are `.cpp`, `.cc` and `.cxx`.
  - Output lines are `file:line: severity: rule: message`, where severity is `error` or `warning`.
  - Checkers that have opt-out markers also take `--verbose`, which lists suppressed findings with their reasons as `file:line: suppressed: rule: message (reason: ...)`. `suppressed` takes the severity's place, so these lines are never read as errors or warnings. The core-purity checker has no opt-outs and no `--verbose`.
  - Exit codes: 0 means no errors (warnings allowed), 1 means at least one error, and 2 means a usage error. A path that doesn't exist, or paths that contain no files the checker reads, is a usage error.
- **Real-time checker:**
  - It strips comments and string literals before matching.
  - It finds real-time bodies by signature and by marker, scanning each body by matching braces:
    - any function named `processBlock`
    - any function named `process` that takes a `ProcessContext` (the SDK's audio callback)
    - any function that carries the real-time marker, a `// realtime` comment alone on its line, before it. Template or return-type lines may sit between the marker and the function's name; a `;`, `{` or `}` between them cancels the marker.
  - It uses the rule set listed in Behaviour. The Plugin Freedom System's real-time hook is the credited starting point; the rule list in this spec is what counts. Rule names are `allocation`, `lock`, `io` and `logging`. Allocation also covers `calloc` and `realloc`; locks cover every standard mutex and lock type. File or network I/O means `fopen`, `fread`, `fwrite`, `fclose`, `fstream`/`ifstream`/`ofstream`, JUCE's `File`, `FileInputStream`, `FileOutputStream` and `URL`, and sockets (`socket`, `StreamingSocket`, `DatagramSocket`).
  - It doesn't follow calls. Real-time code reached only through unmarked helpers isn't scanned, a known limit that `audio-dsp` states.
- **Opt-out marker:** a trailing `// realtime-ok: <reason>` comment suppresses every finding on that line. The reason is required: a tag with no reason suppresses nothing and is itself an error.
- **Core-purity checker:**
  - It strips comments and string literals.
  - It allows C++17 standard headers, plus relative includes that resolve inside the core folder.
  - It reports deprecated C headers (`<math.h>` and the like) as a `warning` that names the `<cmath>`-style replacement.
  - It reports any other include as an error.
  - It reports any `juce::` or `mpc::` name and any `JUCE_` macro, whatever the includes.
  - It reports any source file in the core as a header-only error, including in a core folder that has no headers at all.
- **Example layout:** one example plugin, a tilt EQ, as an effect, with a core, a JUCE wrapper and an MPC wrapper, each in its own folder under the repo's examples area.
  - **The core** smooths the tilt over 20 ms with a one-pole smoother and exposes the smoothed value for the behaviour test. Its `process` function carries the real-time marker.
  - **The core's behaviour test** is a small standalone C++17 program that uses only the standard library, built with the system compiler and run by the check script.
  - **The JUCE wrapper** builds VST3, AU and CLAP from JUCE 9.0.6 plus clap-juce-extensions pinned to a specific tested commit. JUCE is found through a CMake cache variable or an environment variable, never an absolute path. Its UI is a minimal WebView with one tilt control bound to the parameter, using JUCE 9's in-source WebView interop.
  - **The MPC wrapper** is a standard SDK effect project. Its `src/` holds the wrapper source, which includes the core by relative path. Its parameter 0 is the tilt control's partner "output trim" fixed at 0 dB by default, or another control whose small nudge is inaudible. The final choice is made when building it, and checked by inspection.
- **Example check script:**
  - It runs locally on macOS, in the Behaviour order, and never installs anything.
  - It calls the SDK's build tool with absolute paths, `--toolchain zig` and an explicit `--zig <path>` that the script found itself. If zig isn't found, it skips the MPC checks as incomplete.
  - The SDK's own tools may write their cache inside the SDK clone (the accepted trade-off in the capability map). This repo never places its own files there.
  - It checks the Knob FX mapping by reading the MPC project's manifest.
  - It checks "one copy" by searching the source tree for files with the same name as the core headers, and "includes resolve" by resolving each wrapper's include directives relative to the file that contains them.
  - It works out pass, fail or incomplete as stated in Behaviour.
- **The skills give the version-sensitive facts with their source:** JUCE 9.0.6 (no native CLAP yet), the SDK's host contract (44.1 kHz, block sizes, parameter rules, Knob FX). They follow `source-check`, citing official docs and pinning the version.

## Testing

Work type: mixed, so it's split three ways:

1. **Checkers: domain.** Pure text analysis.
2. **Skill content: verified by evals plus inspection.**
3. **Example: technical (managed),** checked against the real toolchains.

Seams:

- **Checker command line → pytest in CI** (a test-only dependency managed with uv; the checkers themselves stay standard-library only). Small fixture source files cover every checker scenario above, one test per scenario. That includes inline `processBlock`, comment and string stripping, the helper `process` method, marked core functions, verbose output and the warning-only exit code. No doubles: the checker reads real files from a temporary folder.
- **`claude plugin eval` cases → the LLM grader.** Run locally before a release; not part of every CI run. One case per scenario:
  - `audio-portable-core`:
    - fires on the share-DSP prompt, with graders for each advice item
    - doesn't fire on a desktop-only reverb
    - doesn't fire on a scaffolded MPC-only project. The scaffold mimics an SDK checkout's layout (a `plugin.json`, `src/` and an empty `tools/` folder) without any SDK files. Accepted as a stand-in.
  - `audio-dsp`:
    - fires on writing a `processBlock`, with graders for each advice item
    - architecture checklist: offered, and no steps or templates offered
    - doesn't fire on the WAV batch converter
  - `audio-parameters`:
    - fires on adding a parameter, with graders for each advice item
    - keep-the-id migration advice for a rename
    - doesn't fire on Claude Code plugin settings
  - shared:
    - no `audio-*` skill fires for "build a Claude Code plugin"
    - no `audio-*` skill fires for "build a Cowork plugin"
- **The example check script → real JUCE, clap-juce-extensions, pluginval, clap-validator, auval, the SDK, zig and `host_sim`,** run on the author's Mac. It's the acceptance check for M1 and M3. It covers every example scenario except the manual ones and parameter 0.

Prior art: the `agent-skills` eval layout and graders (`skill-fired`, criteria graders), and its `sync-references.sh` and `validate-versions.sh`. The version script needs adapting to this repo's three manifests.

Checks other than tests:

- **Inspection in CI:**
  - the sync check (covers shared references drifting)
  - the version check (the three manifests agree)
  - the self-containment check (a skill copied alone)
  - `claude plugin validate`
- **Release checklist, inspected by hand:**
  - install in Claude Code and in Codex, confirm the three skills are listed, and invoke one by name
  - spot-check Copilot, pi and skills.sh once
  - compare skill names with `strangnet-skills` for collisions
  - README contents and Credits, the repo's MIT license, and the Akai notice next to any long quote
- **Manual DAW check:** the WebView control moves the parameter and records automation (Reaper or Live).
- **Manual MPC check:** load on an MPC; the Q-Link changes the sound. It needs hardware, so it's recorded as done or not done in the release notes.
- **Code inspection:** the MPC wrapper's parameter 0 is harmless.
- **M2 and M4 by hand:** build the example a second time with your own `shape`/`spec`/`slice`/`tdd-cycle` flow plus these skills only, in Claude Code. Note where know-how was missing; those notes feed the later specs.

## Boundaries

- Always: the core stays header-only and uses only the standard library, and the core-purity checker passes before any wrapper changes are committed.
- Always: version-sensitive statements in skills cite the official source and the version.
- Ask first: changing the pinned JUCE version or clap-juce-extensions commit.
- Ask first: editing the `strangnet` marketplace in `agent-skills`.
- Ask first: anything that needs patching Akai's SDK, or placing this repo's files inside the SDK clone. The SDK tools' own cache is exempt.
- Never: copy Akai SDK files into this repo.
- Never: have a skill or script install tools.
- Never: add workflow steps, planning templates or state files to a skill.
- Never: duplicate a `strangnet-skills` skill.
- Never: link from a skill to a file outside its own folder.

## Assumptions

- [ ] clap-juce-extensions builds a valid CLAP on JUCE 9.0.6 (M3) → the example check script: the CLAP build plus clap-validator. If it fails, try the latest commit, then pause and re-shape the CLAP route.
- [ ] One unchanged core builds under both wrappers (M1) → the example check script: core purity, both builds, the one-copy check and the include check.
- [ ] The SDK's build tool accepts a project folder outside the SDK clone, and the relative include of the core resolves with the zig toolchain (seen in its arguments, never run) → the first MPC build of the example.
- [ ] pluginval strictness level 10 is achievable for a simple JUCE 9 effect with a WebView editor → the example check script. If level 10 fails for reasons in JUCE itself, record the level reached and why.
- [ ] A Claude marketplace entry without a `version`, pointing at another repo, installs and updates correctly in Claude Code and Copilot → check against the Claude Code plugin docs (`source-check`), then the install check by hand.
- [ ] Signature and marker matching finds the real-time bodies in normal JUCE and SDK code → checker fixtures based on the SDK's examples and JUCE's audio plugin template.

## Out of scope

- `audio-juce`, `audio-juce-webview`, `audio-mpc`, `audio-validation`, `audio-troubleshooting`, `audio-packaging`: later capabilities, in the map's build order.
- Running the example check script in CI on a macOS runner: it needs JUCE, the SDK and zig downloaded on every run; deferred to `validation` or later.
- The Docker and gcc SDK toolchains: the script uses zig only.
- Following calls in the real-time checker: marker-based coverage is enough for now.
- Windows builds of the example: the windows capability.
- The binding checker and the curated JUCE patterns: they belong to `juce`.
- Instruments, MIDI, and AAX, LV2 or AUv3: the example is one effect; formats are limited to VST3, AU and CLAP.
- Signing or notarizing the example: packaging.

## Open questions
