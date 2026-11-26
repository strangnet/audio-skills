# Core layout

## What goes where

| Concern | Core | Wrapper |
|---|---|---|
| DSP: filters, oscillators, nonlinearities, smoothing | yes | no |
| Parameter table: ids, names, ranges, defaults, units, order | yes | builds its host parameters from it |
| Parameter storage, automation, host notifications | no | yes (JUCE `AudioProcessorValueTreeState`, MPC `addParam`/`get`) |
| Converting host buffers to `float* const*` | no | yes |
| In-place handling: copy inputs to outputs when they differ | no | yes |
| Sample rate and maximum block size | received in `prepare` | passes them in |
| Allocation | only in `prepare` | only in prepare |
| Denormal flush-to-zero around the callback | no (lets its own state reach zero) | yes |
| Latency in samples | computes and exposes it | reports it to the host |
| Saved state, presets, programs | no | yes, keyed by the core's parameter ids |
| UI, editor, Knob FX mapping | no | yes |

## Interface sketch

A small, plain interface that both wrappers can drive the same way:

```cpp
// core/tilt_eq.h: header-only C++17, standard library only.
#pragma once
#include <array>
#include <cmath>

namespace tilt {

struct ParamInfo { const char* id; const char* name; float min, max, def; const char* unit; };

enum Param { kOutput = 0, kTilt, kNumParams };

// The one definition of the parameters: stable ids, fixed order. Row 0 is harmless.
inline constexpr std::array<ParamInfo, kNumParams> kParams {{
    { "output", "Output", -12.0f, 12.0f, 0.0f, "dB" },
    { "tilt",   "Tilt",   -12.0f, 12.0f, 0.0f, "dB" },
}};

class TiltEq {
public:
    void prepare(double sampleRate, int maxBlockSize);  // allocate and compute coefficients here
    void reset();                                       // clear state; snap smoothers to targets
    void setParam(int index, float plainValue);         // plain units, any thread-safe source
    int latencySamples() const;                         // the wrapper reports this to the host

    // realtime
    void process(float* const* channels, int numChannels, int numFrames);  // in place
};

}  // namespace tilt
```

- **In place.** `process` reads and writes the same buffers. JUCE's `processBlock` gives one buffer for input and output; the MPC usually does too. The wrapper copies an input to its output only when the pointers differ, then calls the core on the outputs.
- **Plain units.** Parameters arrive in dB, Hz or percent, not normalised 0 to 1. Each host does its own normalising; the core doesn't know about it.
- **Any block size.** `numFrames` can be anything up to the maximum passed to `prepare`. The MPC calls with 32 to 512.
- **Channels.** The core holds state for a fixed maximum number of channels and ignores extras, or the wrapper only offers layouts the core supports.
- **The sample rate comes from `prepare`.** Never hard-code 44100.

## Testing the core on its own

Because the core needs nothing but a compiler, its behaviour can be tested by a small standalone program, such as `c++ -std=c++17 tests/core_test.cpp && ./a.out`, with no JUCE and no SDK. Test what both targets rely on: unity at neutral settings, the direction of each control, smoothing times, and silence decaying to exact zero. Then each wrapper's own validator (pluginval, clap-validator and auval on the desktop; the SDK's `host_sim` for the MPC) checks only the conversion layer.

## Folder layout

```
my-plugin/
├── core/            # the only copy of the DSP: headers only
│   └── tilt_eq.h
├── tests/           # the core's behaviour test, plain C++
├── juce/            # JUCE wrapper: CMakeLists.txt, Source/
└── mpc/             # MPC wrapper: an SDK project, plugin.json, ui.json, src/
```

`juce/Source/PluginProcessor.h` includes `"../../core/tilt_eq.h"`, and so does `mpc/src/TiltEq.cpp`. Both paths are relative to the including file, and both resolve to the same file.
