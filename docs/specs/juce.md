# Spec: juce, V1

Status: approved
Source: [capability map](audio-skills-map.md) (juce); conversation, 2026-11-27; a review of the Plugin Freedom System's JUCE material against JUCE 9.0.6

## Problem

Agents write JUCE plugins from memory of JUCE 6, 7 and 8. The code compiles, then fails in ways that are slow to trace:
- a random plugin code that changes on every configure
- an effect with no input bus
- an instrument that the host lists as an effect
- a WebView UI whose knobs don't move, or that shows a blank page

The WebView failures are the worst, because JUCE reports most of them only as a console warning inside the web view, or not at all.

The Plugin Freedom System holds the best collection of fixes, but it targets JUCE 8, only works in Claude Code, and some of its rules are wrong for JUCE 9.0.6:
- the third attachment argument
- `NEEDS_WEB_BROWSER` as the cause of a missing VST3
- `getNumPrograms()` returning 0
- the separate native-interop file
- an invented event format

The foundation's example wrapper was written without any JUCE skill, and what was learned there is in nobody's skill yet.

Success: an agent that loads these skills sets up a JUCE 9 plugin and a WebView editor that work the first time, and the binding checker catches the silent binding failures (mismatched relay names or types, a wrongly loaded library) before the plugin is loaded in a host.

## Solution

Two more skills join the package:

- **`audio-juce`**: building a JUCE 9 plugin with CMake. It covers:
  - the formats: VST3 and AU from JUCE, and CLAP through clap-juce-extensions
  - plugin codes, bus layouts for effects and instruments, and the parameter tree
  - which thread does what
  - the editor's lifecycle, state, and the host-facing pitfalls
- **`audio-juce-webview`**: a WebView editor in JUCE 9. It covers:
  - serving the page from inside the plugin, and the JavaScript interop library
  - relays and attachments, gestures, and what fails silently
  - a **binding checker** that compares the relays the C++ side creates with the states the page requests, and checks how the page loads JUCE's library

The tilt-EQ example's JUCE wrapper passes the binding checker, and the example check script runs it.

## Scope

This version covers macOS, JUCE 9.0.6 and the WebView editor route. Its riskiest assumption is that a source-only checker can catch the silent binding failures in normal JUCE code without false alarms. The example, JUCE's own WebView plugin demo and the Plugin Freedom System's plugins give real code to test that against. Windows (WebView2), Component-based editors, and installing plugins and clearing host caches come later; see Out of scope.

## Behaviour

### As a developer, I want JUCE 9 know-how in the agent, so that my plugin builds, loads and behaves in every host the first time

- Given a prompt to set up a JUCE plugin project (CMake, formats, the processor), or to fix one (an effect that gets no input, a plugin that appears twice in the host), then `audio-juce` fires.
- When it fires, then its advice covers:
  - JUCE found through a CMake cache variable or an environment variable, never an absolute path
  - a fixed, unique four-character plugin code and manufacturer code. If the plugin code is left out, JUCE 9 picks a random one that changes on every configure. For AU, the plugin code needs exactly one upper-case letter, and the manufacturer code at least one.
  - module headers rather than the generated `JuceHeader.h`, which is optional and needs its own CMake call
  - CLAP through clap-juce-extensions pinned to a tested commit, because JUCE 9.0.6 has no native CLAP
  - the bus layout matching the plugin type: an effect declares an input bus. An instrument sets the synth flag and MIDI input, and declares output buses only. Changing the VST3 categories alone doesn't fix a mismatch.
  - parameters created with a `ParameterID` that carries a version hint, which sets AU parameter ordering, and built from the core's parameter table when there is one
  - the audio thread reading parameters through cached raw-value atomics. Parameter value reads don't lock; the cache saves the lookup.
  - the editor never calling into the audio callback. It talks to the audio thread through parameters, atomics or a lock-free FIFO.
  - the editor being destroyed and recreated whenever its window closes, so anything it needs to rebuild lives in the processor or its state
  - at least one program from `getNumPrograms()`, with `setCurrentProgram` a no-op for a plugin without programs, because some hosts call it after restoring state
  - renaming the product leaving the old bundles installed, and hosts loading installed bundles, not the build folder
- Given a prompt about a WebView editor, then `audio-juce` leaves the editor's details to `audio-juce-webview`.
- Given a prompt about a Component-based editor, then `audio-juce` says it doesn't cover them and points to JUCE's documentation, with no Component-specific advice.
- Given a prompt to write an instrument, then the advice covers the synth flag, MIDI input and output-only buses, and the pitfall of an instrument the host lists as an effect and that gets no MIDI.
- Given the agent is working inside an Akai SDK checkout on an MPC-only plugin, then `audio-juce` doesn't fire.
- Given a prompt about an audio plugin in another framework (iPlug2, nih-plug), then `audio-juce` doesn't fire.

### As a developer, I want WebView editor know-how in the agent, so that the UI loads and its controls move the parameters

- Given a prompt to build, wire up or debug a JUCE WebView editor (a blank page, knobs that don't move, automation that isn't recorded), then `audio-juce-webview` fires.
- When it fires, then its advice covers:
  - serving the page through the resource provider and its root URL, not a file URL. A file URL needs the files installed at a known path, and the macOS web view blocks access to the page's sibling files by default. The root arrives at the provider as `/`.
  - an explicit map from URL to embedded file with the right MIME type, because embedded binary data flattens file names
  - JUCE's interop library taken from the same JUCE version, from the JUCE checkout or the matching npm package. JUCE 9 compares the two versions at runtime. JUCE 9's built library bundles its native-interop check, so the page loads a single file; JUCE 8's library imported a second file that also had to be served.
  - loading the library as an ES module and importing from it, not from `window.__JUCE__`
  - each relay constructed with its name and registered with the browser options
  - each relay declared before the browser, so it outlives the browser that holds its options, and each attachment declared after its relay. Relays, browser, then attachments is the usual order. In JUCE 9.0.6, an attachment declared before the browser is safe.
  - JavaScript state types matching the relay types: slider, toggle or combo box
  - value-changed listeners that take no arguments and read the value inside the listener
  - drag start and drag end calls around each user edit, so the host records one gesture
  - a state name the C++ side doesn't know only logging a console warning: the usual silent cause of a frozen control
  - native integration enabled only for the plugin's own content, and navigation kept on the plugin's page
  - native function and event callbacks running on the message thread, and events sent only after the first page load
  - running the binding checker
- Given a prompt about a WebView editor on Windows, then the skill says Windows isn't covered yet. It gives no WebView2 advice.
- Given a prompt to build an ordinary web page or web app with a slider, then `audio-juce-webview` doesn't fire.
- Given advice the Plugin Freedom System gives that JUCE 9.0.6 contradicts, then the skill states the 9.0.6 behaviour. It never repeats the old rule.

### As a developer or an agent, I want to check that a WebView editor's C++ and page agree, so that silent binding failures are caught before a host loads the plugin

- Given an editor whose relay names and types match the page's state requests, and whose page loads the library correctly, when the binding checker runs on the editor sources and the UI folder, then it reports no findings and exits with success.
- Given a C++ relay whose name no JavaScript state requests, or a JavaScript state whose name no relay has, when it runs, then it reports each one with `file:line`, rule `relay-name`, and exits with failure.
- Given a relay requested with the wrong state type (a slider relay read with the toggle state), when it runs, then it reports rule `relay-type` and exits with failure.
- Given a page that loads the interop library without `type="module"`, when it runs, then it reports rule `module` and exits with failure.
- Given a page that imports a name the interop library doesn't export, or calls one through the library's namespace import (`Juce.getSlidrState`), when it runs, then it reports rule `module` and exits with failure.
- Given a page that calls a state function through `window.__JUCE__`, when it runs, then it reports rule `module` and exits with failure. Other uses of `window.__JUCE__`, such as listening for backend events, aren't reported.
- Given names that aren't string literals on one side for one relay type (C++ relays built in a loop from the core's parameter table, or a page calling `getSliderState(id)` in a loop), when it runs, then it reports one `warning`, rule `relay-name`, saying the names on that side can't be matched. It reports no unmatched names on the other side for that type, because any of them might be among the computed ones. Literal names that don't match are still reported when both sides use only literals. Warnings alone exit with success.
- Given a page written in TypeScript or JSX (a bundler builds it), when it runs on the source folder, then it reads the state calls there as it does in JavaScript.
- Given a copy of JUCE's interop library inside the UI folder, including JUCE 8's separate native-interop file, when it runs, then it doesn't scan those files as page code.
- Given a relay name, `type="module"` or a state call that appears only in a comment, in a JavaScript string that isn't a state-call argument or import, or in the page's visible text, when it runs, then it doesn't count it.
- Given a folder that holds dependencies or build output (`node_modules`, a CMake build folder), when it runs on a parent folder, then it doesn't read them.
- Given a path that doesn't exist, or paths with no C++ files or no page files, when it runs, then it prints usage and exits with the usage-error code.

### As the package author, I want the example's JUCE wrapper held to the new skills, so that the skills are proven on a real build

- Given the tilt-EQ example, when its check script runs, then the binding checker passes on the JUCE wrapper's editor and UI folder, and the summary lists it as a check.
- Given the binding checker's checks are added, then every existing example check still passes.

## Decisions

- **Two skills, split by concern:** `audio-juce` holds the processor, CMake, formats and host-facing facts; `audio-juce-webview` holds the editor and the page. Where an advice item touches another skill's ground (the parameter version hint, raw-value atomics, FIFOs to the UI), the JUCE skill states the JUCE API in a line or two and refers to `audio-parameters` or `audio-dsp` by name for the reasoning. It doesn't repeat their design or real-time rules.
- **Pinned versions:** JUCE 9.0.6, and the clap-juce-extensions commit the foundation's example already uses. Every version-sensitive fact cites the JUCE document or source file it comes from (`source-check`).
- **Curated Plugin Freedom System material:** only technical facts carry over, each checked against JUCE 9.0.6. Its workflow parts are left out: stages, agent roles, reports, install scripts and registries. Its rules that are wrong for 9.0.6 are left out, or corrected where a real pitfall sits behind them (the host that resets the program after restoring state).
- **The binding checker lives in `audio-juce-webview`** and follows the shared checker interface:
  - Python 3, standard library only, source only
  - output as `file:line: severity: rule: message`
  - exit codes 0, 1 and 2
  - no opt-outs and no `--verbose`, like the core-purity checker

  It reads C++ headers and sources with the same suffixes as the other checkers. Page files are `.html`, `.htm`, `.js`, `.mjs`, `.ts`, `.tsx` and `.jsx`.
  - **C++:** it strips comments and string literals, except relay names.
  - **JavaScript and TypeScript:** it strips comments and string literals, except the argument of a state call and an import specifier.
  - **HTML:** it reads only `script` elements and their `src` attributes. Comments and visible text are ignored.
  - **Folders:** it searches folders recursively, but skips `node_modules`, `.git`, and any folder holding a `CMakeCache.txt` or named `_deps`. Files given by name are always read.
- **C++ side:** the checker doesn't parse classes or members. A relay is a construction of one of JUCE's three relay classes: a declaration, a brace or parenthesis initialiser, or a `make_unique` of the class. Its name is the string literal passed to it. A relay class constructed with anything other than a literal (a variable, a table lookup, a loop) makes that type's C++ names computed.
- **Page side:**
  - The state functions are `getSliderState`, `getToggleState` and `getComboBoxState`. A call to one of them is a state request, whether it is called bare, through a named import (including one renamed with `as`), or through a namespace import.
  - The interop library is recognised by content: a file that defines the state functions, or JUCE 8's native-interop check file, is part of the library and isn't scanned as page code.
  - A script or import loads the library when its specifier resolves to such a file, names the npm package, or is the one the page's state functions are imported from. That covers the example, which serves the library from the JUCE checkout and has no copy of it in the UI folder.
  - Names imported from the library, and members called through its namespace, are checked against the export list the checker carries, never against a vendored copy.
- **What the checker can't see,** stated in the skill:
  - relay registration with the browser options, member declaration order, native integration and loading the provider's root: the skill states each as a rule to follow, because checking them needs C++ member parsing that real editor layouts kept defeating
  - parameter ids, because they're often built at runtime
  - whether every file the page references is served by the resource provider
  - native functions and events
  - gesture calls
  - modules beyond the page's own files
- **The interop library's export list is checked against JUCE 9.0.6:** `getNativeFunction`, `getSliderState`, `getToggleState`, `getComboBoxState`, `getBackendResourceAddress` and `ControlParameterIndexUpdater`. The checker carries that list and cites its source.
- **Install and host caches:** `audio-juce` states that hosts load installed bundles and cache their scans, and that renaming the product leaves the old bundles installed. The details (paths, clearing caches, signing for local tests) belong to `audio-validation`.
- **JUCE's license:** skills paraphrase JUCE's documentation and source and cite them. They never quote JUCE source at length.
- **Credits:** the README's Plugin Freedom System credit also names its troubleshooting patterns, as the source of the curated JUCE material.

## Testing

Work type: mixed, split as in the foundation:
1. **Binding checker:** domain.
2. **Skill content:** evals plus inspection.
3. **Example:** technical (managed).

Seams:
- **Binding checker command line → pytest in CI.** Small fixture folders cover every checker scenario, one test per scenario, with no doubles. The passing fixtures follow the real layouts of the tilt-EQ example, JUCE's WebView plugin demo (a TypeScript page with computed names) and two Plugin Freedom System editors (relays created through `make_unique`, several per declaration, and state names requested in a loop).
- **`claude plugin eval` cases → the LLM grader,** run locally before a release:
  - `audio-juce`:
    - fires on setting up a JUCE 9 plugin for VST3, AU and CLAP, with graders for each advice item
    - fires on fixing an effect that gets no input in the host, and on a plugin that appears twice in the host
    - instrument advice for a synth prompt
    - leaves a WebView editor question to `audio-juce-webview`
    - on a Component-based editor, says it isn't covered and gives no Component advice
    - doesn't fire on a scaffolded MPC-only SDK project
    - doesn't fire on an iPlug2 or nih-plug plugin
  - `audio-juce-webview`:
    - fires on adding a WebView editor to a JUCE plugin, with graders for each advice item
    - fires on frozen knobs, on a blank WebView page and on automation that isn't recorded
    - Windows says not covered yet
    - doesn't fire on an ordinary web slider
  - the shared "Claude Code plugin" and "Cowork plugin" cases keep passing, with no `audio-*` skill firing
- **The example check script → real JUCE 9.0.6.** It runs the binding checker on the JUCE wrapper, next to the existing checks. A test in the example's check-script tests asserts that the binding check is in its check list.
- **The binding checker on the real example → pytest in CI.** It needs no JUCE build, so a test runs it on the example's editor and UI folder and expects success, as the other checkers' tests already do for the example's core and wrappers.

Prior art:
- the real-time and core-purity checkers and their pytest suites (fixture layout, the usage-error tests)
- the foundation's eval cases and scaffold scripts
- the example check script's check list

Checks other than tests:
- **Inspection:**
  - every version-sensitive statement cites a JUCE 9.0.6 document or source file
  - no Plugin Freedom System rule that 9.0.6 contradicts appears in either skill, and each corrected rule in the Behaviour list is present
  - neither skill repeats `audio-parameters`' or `audio-dsp`'s design or real-time rules beyond the one- or two-line API statement allowed under Decisions
- **Inspection in CI:** the existing sync, version, self-containment and plugin-validate checks cover the two new skill folders.

## Boundaries

- Always: check a JUCE fact against the 9.0.6 checkout or docs before writing it into a skill.
- Always: the example's JUCE wrapper passes the binding checker before the skill is called done.
- Ask first: changing the pinned JUCE version or clap-juce-extensions commit.
- Ask first: changing the example's UI beyond what the binding checker needs.
- Never: copy the Plugin Freedom System's workflow parts: stages, agent roles, state files, install scripts.
- Never: quote JUCE source at length.
- Never: have a skill or the checker install anything.

## Assumptions

- [ ] Matching relay constructions and page state requests finds the names in normal JUCE editor code → passing fixtures built from the tilt-EQ example, JUCE's WebView plugin demo and two Plugin Freedom System editors. Any real editor the checker misreads during the build becomes a fixture, and the spec is amended first.
- [ ] Problems found once the skills are in real use are fed back into the skills and the checker, as deltas to this spec.
- [ ] The interop library's export list doesn't change across 9.0.x patch releases → recheck whenever the JUCE pin changes (already "Ask first").
- [ ] The M2/M4 run hasn't happened yet. Its notes may add JUCE items, which then come in as a delta to this spec, not a rewrite.

## Out of scope

- Windows and WebView2 (the backend choice, the user data folder, static linking): the windows capability. The facts are already checked against 9.0.6 and noted for it.
- Component-based editors (attachments for JUCE sliders, LookAndFeel, layout): not used by the example, and the WebView route was chosen.
- Installing plugins, clearing host caches and signing for local tests: `audio-validation`.
- AAX, LV2, AUv3, VST2 and standalone builds.
- Checking parameter ids against the parameter tree, native functions and events, and gesture calls: the core checker set was chosen, and ids are often built at runtime.
- Checking relay registration, member order and browser setup (`relay-options`, `member-order`, `browser-setup`): three review rounds found real editor layouts (members through smart pointers, several per declaration, names assigned in constructor bodies, options built in helpers) that a source-only member parser misread. The skill states these as rules; a later version can add them if real use shows the need.
- Checking that every file the page references is served (an `asset` rule): real resource providers forward to other functions, mix MIME types with paths and read zips, so a source-only rule raised false alarms. The skill covers serving files instead.
- A second example plugin with toggle and choice controls: fixtures cover those relay types.
- UI craft advice (relative knob drags, animation loops, hover effects): not verified as rules.
- DSP technique recipes: the candidate `dsp-recipes` capability.

## Open questions
