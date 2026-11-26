# Glossary

**Target**: where a plugin runs. There are two: *desktop* (VST3, AU and CLAP built with JUCE, on macOS and later Windows) and *MPC* (a VST2 `.so` for Akai's standalone MPC hardware, built with Akai's SDK). A plugin can have one target or both.

**Core** (portable DSP core): the plugin's audio processing and parameter model, written as header-only C++17 that uses only the standard library. It knows nothing about JUCE or MPC. Don't call it "engine" or "shared library".

**Wrapper**: the code that adapts the core to one target's plugin API. The *JUCE wrapper* is an `AudioProcessor` plus editor. The *MPC wrapper* is an `mpc::Plugin` subclass. Each target has exactly one wrapper, and wrappers never share code with each other, only the core.

**Audio callback**: the function a host calls on the real-time audio thread. That's `processBlock` in a JUCE wrapper and `process` in an MPC wrapper. Real-time rules apply inside it.

**Checker**: a standalone Python 3 script that uses only the standard library. It reads plugin source code and reports problems with `file:line`. It reads only source code, never workflow files such as briefs or plans.

**Skill**: one folder under `skills/` with a `SKILL.md`. It holds know-how only, never a workflow. Every skill in this package is named `audio-*`.

**Know-how**: technical facts, rules and pitfalls about audio and plugin development. It's the opposite of *workflow*: the order in which work is done, which the user chooses.

**SDK** (Akai SDK): the user's own clone of Akai's MPC Plugin Builder SDK, found through `$MPC_SDK`. This package never copies it.
