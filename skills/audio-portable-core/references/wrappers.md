# Wrappers

Each wrapper is thin: it converts its host's types into the core's plain ones, and holds everything host-specific. JUCE facts are checked against JUCE 9.0.6, and SDK facts against the Akai MPC Plugin SDK at commit e78bad5 (see Sources).

## JUCE wrapper

- **Include:** `#include "../../core/tilt_eq.h"` from `juce/Source/`. Don't add the core folder to `target_include_directories`. A bare `#include "tilt_eq.h"` would then work on the desktop and fail in the SDK build, and the two wrappers would no longer show the same path.
- **Parameters:** build the `AudioProcessorValueTreeState::ParameterLayout` by looping over the core's table. Use `juce::ParameterID { p.id, 1 }` and a `NormalisableRange` from `p.min` and `p.max`, with the skew the spec gives.
- **`prepareToPlay(sampleRate, samplesPerBlock)`:** call `core.prepare(sampleRate, samplesPerBlock)`, then report `core.latencySamples()` with `setLatencySamples`.
- **`processBlock`:**
  1. Start with `juce::ScopedNoDenormals`.
  2. Read each parameter once with `getRawParameterValue(id)->load()` and pass it to `core.setParam`.
  3. Call `core.process(buffer.getArrayOfWritePointers(), numChannels, buffer.getNumSamples())`.
- **State:** save and load the value tree. It's keyed by the same ids as the core's table.

## MPC wrapper (SDK project)

- **Project shape:** a standard SDK effect project. `plugin.json`, `ui.json` and `src/<Name>.cpp` sit in the wrapper folder. The SDK's `tools/build.py` compiles only `<project>/src/*.cpp`. Its include path holds only the SDK's `framework/` and the project's `src/`, and it has no option to add another folder (`--define` sets macros only). So the core can't be put on the include path; a relative include from `src/` is the way in: `#include "../../core/tilt_eq.h"`.
- **Building from outside the SDK:** call the SDK's build tool with absolute paths, such as `python3 <sdk>/tools/build.py <abs project> --target all --toolchain zig --zig <abs zig>`. The tool writes its output into `<project>/build/`, so ignore that folder in version control. With no zig on `PATH`, `$ZIG` or `--zig`, it installs one into the SDK clone.
- **Parameters:** in the constructor, loop over the core's table, calling `addParam(mpc::floatParam(p.id, p.name, p.min, p.max, p.def, p.unit, decimals))`. Use `mpc::logParam` for frequencies and times. The table's order becomes the MPC's parameter indices, which the Knob FX mapping in `plugin.json` refers to.
- **`prepare(sampleRate, maxBlockSize)`:** call `core.prepare(sampleRate, maxBlockSize)`. Set `PluginInfo::latencySamples` from the core in `makeInfo()`, because the host reads latency at load.
- **`process(mpc::ProcessContext& ctx)`:**
  1. Use `min(numInputs, numOutputs)` channels.
  2. For each one, copy `ctx.inputs[ch]` into `ctx.outputs[ch]` only when the pointers differ.
  3. Read the parameters once with `get(index)` and pass them to `core.setParam`.
  4. Call `core.process(ctx.outputs, channels, ctx.numFrames)`.

  The framework already flushes denormals around `process()`.
- **Checking it:** the SDK's `host_sim test` on the native build checks:
  - block sizes 32 and 512
  - in-place and separate buffers
  - the parameter 0 nudge
  - state round-trips
  - denormals

## Both wrappers

- No DSP in the wrappers beyond copying buffers. Anything that shapes the sound goes in the core, so the targets match.
- The same parameter order on both. The JUCE host matches by id, and the MPC matches by index, so both must come from the core's table.

## Sources

- Akai MPC Plugin SDK (version 1.0 plus the unreleased 1.1 changes, commit e78bad5, 2026-11-23; MIT, copyright (c) 2026 inMusic Brands, Inc.), paraphrased:
  - `tools/build.py`: `find_sources` compiles only `<project>/src/*.cpp`, the include path is the SDK's `framework/` plus the project's `src/`, output goes to `<project>/build/`, and zig lookup and installation.
  - `framework/mpc_plugin.h`: `ProcessContext` (in-place note), `floatParam` and `logParam`, `PluginInfo::latencySamples`, `ScopedDenormalsOff`.
  - `docs/host-contract.md`: latency read at load, block sizes.
  - `tools/host-sim/README.md`: what `host_sim test` checks.
- JUCE 9.0.6: `juce_AudioProcessor.h` (`setLatencySamples`), `juce_AudioProcessorValueTreeState.h`, `juce_FloatVectorOperations.h` (`ScopedNoDenormals`).
- This package's tilt-EQ example (`examples/tilt-eq/` in the strangnet-audio-skills repo) builds this layout end to end on both targets.
