---
name: audio-dsp
description: Real-time DSP know-how for audio plugins on desktop (JUCE VST3, AU, CLAP) and Akai MPC hardware, covering real-time safety in the audio callback and the code it calls, denormals, parameter smoothing, aliasing and oversampling, latency reporting, variable block sizes, a CPU budget per target, a DSP architecture checklist, and a real-time checker script. Use when writing, reviewing or debugging an audio callback (JUCE `processBlock`, or `process(ProcessContext&)` in an MPC wrapper) or the DSP core it calls; when sound glitches, clicks, zippers, aliases or eats CPU; when adding oversampling, a lookahead or anything that adds latency; or when planning a plugin's signal chain and DSP. Not for work inside an Akai MPC SDK checkout that Akai's own `mpc-plugin-dsp` skill already covers (use that there). Not for offline audio-file processing with no plugin (batch converters, WAV scripts), and not for Claude Code or Cowork plugins.
---

# Audio DSP

A plugin's audio callback runs on the host's real-time thread with a hard deadline: a few milliseconds per block, on every block, forever. Missing it once is an audible dropout. Anything that can wait on another thread, the allocator, the disk or the network can miss it, however rarely. The rules below apply to the callback **and to every function it calls**, including the portable DSP core.

## Rules for the audio callback

- **No allocation, locks, blocking I/O or logging** in the callback or anything it calls: no `new`/`malloc`, no container growth (`push_back`, `resize`), no `std::string` building, no mutex, no file or network access, no `printf`/`DBG`/logger. Allocate and size everything in prepare (`prepareToPlay` in JUCE, `prepare` in the MPC SDK), which runs before audio starts. Pass parameters to the audio thread through atomics.
- **Protect against denormals.** Wrappers switch flush-to-zero on around the callback (JUCE `juce::ScopedNoDenormals`; the MPC SDK framework does it for you). The core should still let decaying state reach exact zero, because flush-to-zero only removes true subnormals and the core may run without it.
- **Smooth every audible parameter.** Gain, cutoff, mix and the like glide to a new value over 10 to 50 ms. Read each parameter once per block, then smooth per sample.
- **Mind aliasing.** Nonlinear stages (saturation, waveshaping, hard clipping) and naive oscillators create harmonics above Nyquist that fold back as inharmonic noise. Oversample nonlinear stages, or use band-limited methods.
- **Report latency.** Anything that delays the signal (oversampling filters, lookahead, FFT blocks, linear-phase filters) must be reported to the host in samples, so it can compensate.
- **Handle any block size.** The size announced in prepare is a maximum, not a promise. The MPC calls with anything from 32 to 512 frames. Never assume a fixed block, and never read past `numFrames`.
- **Fit the CPU budget of the slowest target.** The 32-bit MPCs (Cortex-A17) set the limit: aim for a whole plugin under about 15% of a 128-frame block, worst case.
- **Run the real-time checker** on the wrapper and on the core (below). It catches the obvious mistakes, not all of them.

Details, numbers and sources: [references/realtime-rules.md](references/realtime-rules.md), [references/dsp-quality.md](references/dsp-quality.md) and [references/mpc-audio.md](references/mpc-audio.md).

## The real-time checker

`scripts/check_realtime.py` (Python 3, standard library only) scans source code for allocation, locks, I/O and logging in real-time bodies:

```bash
python3 scripts/check_realtime.py [--verbose] <file-or-folder>...
```

Run it with this skill's folder as the base, on the wrapper folder **and** the core folder. It scans every `processBlock`, every `process(ProcessContext&)`, and every function marked with a `// realtime` comment on the line before it. Mark the core's entry points, because the checker **doesn't follow calls**. Output is `file:line: severity: rule: message`. Exit 0 means no errors (warnings are allowed), 1 means errors, and 2 is a usage error. Markers, opt-outs and limits: [references/realtime-rules.md](references/realtime-rules.md).

## Planning the DSP

When planning a plugin's DSP, go through [references/architecture-checklist.md](references/architecture-checklist.md). It covers the signal chain, mono or stereo layout, latency, oversampling, sample-rate dependence (the MPC is fixed at 44.1 kHz) and the CPU budget. It is a list of questions to answer, not a process: use whatever planning approach you already have.

## References

Read only what the task needs:

- [references/realtime-rules.md](references/realtime-rules.md): what is forbidden and why, what the checker catches and misses, the marker and opt-out.
- [references/dsp-quality.md](references/dsp-quality.md): denormals, smoothing, aliasing and oversampling, latency, and block sizes, with JUCE 9.0.6 specifics.
- [references/mpc-audio.md](references/mpc-audio.md): the MPC's sample rate, block sizes, in-place buffers, CPU budget and denormal handling, with SDK sources.
- [references/architecture-checklist.md](references/architecture-checklist.md): the DSP architecture questions.

## Pitfalls

- A clean `processBlock` that calls a core function which allocates. Mark the core's entry points so the checker scans them.
- Copying a temporary `std::vector` or `juce::AudioBuffer` inside the callback "just for this block".
- Smoothing in the wrapper on one target and in the core on another, so the two sound different.
- Computing filter coefficients from a hard-coded 44100, which is right on the MPC and wrong on the desktop.
- Oversampling without reporting the filter latency.
- Assuming the announced block size and indexing a scratch buffer past `numFrames`, or sizing it smaller than the largest block.
