---
name: audio-portable-core
description: How to structure one DSP core that ships behind both a JUCE plugin (VST3, AU, CLAP) and an Akai MPC plugin, covering a header-only, standard-library-only C++17 core, relative includes from each wrapper, keeping host types out of the core, the real-time marker, defining parameter ids and order once, and a core-purity checker script. Use when sharing DSP between a desktop plugin and an MPC plugin, porting a JUCE plugin's DSP to the MPC (or the reverse), splitting DSP out of a `processBlock` or `process(ProcessContext&)` into a reusable core, or reviewing whether a core is portable. Not for a desktop-only plugin with no MPC target, and not for an MPC-only plugin inside an Akai MPC SDK checkout, which Akai's own `mpc-plugin-*` skills cover (use those there). Not for Claude Code or Cowork plugins.
---

# Audio portable core

One DSP implementation, two very different hosts. A JUCE plugin hands the code a `juce::AudioBuffer` through CMake; an MPC plugin hands it a `ProcessContext` through Akai's own build tool, which compiles only the project's `src/` folder. The way to share DSP between them is a **core** that knows about neither: a few headers with plain inputs and outputs. Each target gets a thin **wrapper** that converts between its host and the core.

## Rules

- **Header-only C++17, standard library only.** The core is one or more `.h` files with no `.cpp`, and its only includes are standard headers (`<cmath>`, not `<math.h>`) and its own headers. Any other dependency would have to build under both CMake and the SDK's build tool, for desktop and for ARM.
- **Each wrapper includes the core by a relative path** from its own source folder, such as `#include "../../core/tilt_eq.h"` from `mpc/src/`. The SDK build compiles only `<project>/src/*.cpp`, puts only its own `framework/` and the project's `src/` on the include path, and has no option to add another folder. A relative path works there and under CMake alike. Keep exactly one copy of the core. Never copy it into `src/`.
- **The core never sees host types.** No `juce::`, no `mpc::`, no `JUCE_` macros, and no host buffer, parameter or context types. The wrapper converts host buffers into `float* const*` with a channel and frame count, host parameters into plain values in real units, and passes the sample rate to `prepare`.
- **Mark the core's real-time entry points** with a `// realtime` comment on the line before them, so the `audio-dsp` skill's real-time checker scans them. That checker doesn't follow calls from the wrapper into the core.
- **Define parameter ids and order once, in the core.** A table in the core lists each parameter's stable id, name, range, default and unit, in its fixed order. Both wrappers build their parameter lists from that table, so the JUCE ids and the MPC indices can't drift apart. Row 0 must be harmless; see the `audio-parameters` skill.
- **Run the core-purity checker** on the core folder (below).

What the core and each wrapper hold, and an interface sketch: [references/core-layout.md](references/core-layout.md). How each wrapper connects to it: [references/wrappers.md](references/wrappers.md).

## The core-purity checker

`scripts/check_core_purity.py` (Python 3, standard library only) reads the core's source code:

```bash
python3 scripts/check_core_purity.py <core folder>...
```

Run it with this skill's folder as the base. It strips comments and string literals, then reports, as `file:line: severity: rule: message`:
- `include`: any include that isn't a standard C++17 header or a file inside the core
- `juce-name`, `juce-macro` and `mpc-name`: any `juce::` name, `JUCE_` macro or `mpc::` name, even with no matching include
- `header-only`: any source file (`.cpp`, `.cc`, `.cxx`) in the core
- `deprecated-header`, as a warning: a C header such as `<math.h>`, naming its replacement (`<cmath>`)

Headers are `.h` and `.hpp`. Exit 0 means no errors (warnings are allowed), 1 means errors, and 2 is a usage error. A pure core can still break real-time rules: the standard library includes `<mutex>`, `<fstream>` and `<iostream>`. Run the real-time checker as well.

## Pitfalls

- A `prepare` that takes `juce::dsp::ProcessSpec`, or a `process` that takes `juce::AudioBuffer`: the core no longer builds for the MPC.
- `#include <JuceHeader.h>` "just for `jmap`" or `MathConstants`. Write the three lines yourself.
- Adding the core folder to the JUCE target's include path and writing `#include "tilt_eq.h"`. It works on the desktop, then fails in the SDK build.
- Parameter lists written out separately in each wrapper, so a later change updates one and not the other.
- Smoothing in one wrapper and not the other, so the two targets sound different. Smooth in the core.
- Hard-coding 44100 because the MPC is fixed at 44.1 kHz. The desktop isn't.
