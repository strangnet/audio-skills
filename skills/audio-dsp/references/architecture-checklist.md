# DSP architecture checklist

Questions to answer before writing a plugin's DSP. They are not steps and have no required order or document format: answer them in whatever plan, issue or conversation you already use. An unanswered question is a decision that will be made by accident later.

## Signal chain

- What are the processing stages, in order, from input to output? Draw it as a line of boxes.
- Which stages are linear (gain, EQ, filters, delay) and which are nonlinear (saturation, clipping, compression, modulated delay)?
- Where do the parameters act? Is each one per sample, per block, or applied only in prepare?
- Is there feedback? What bounds its gain below 1?
- Is there a dry/wet mix? If the wet path has latency, the dry path must be delayed to match.

## Channel layout

- Mono, stereo, or both? Which input/output layouts will the wrapper accept?
- Is stereo processing linked (one detector or modulator for both channels) or independent?
- Is there mid/side processing, a stereo width control, or mono compatibility to keep?
- How many channels does the core hold state for, and what happens with more?
- On the MPC: effects are stereo in, stereo out.

## Latency

- Does any stage delay the signal: oversampling filters, lookahead, FFT blocks, linear-phase filters?
- What is the total in samples, and does it change with a parameter or the sample rate?
- Where is it reported to the host, and when is it updated?

## Oversampling

- Which nonlinear stages alias audibly at 44.1 kHz?
- Which factor do they need (2x, 4x, 8x), or is a band-limited method cheaper?
- Is oversampling applied only around the nonlinear stage, not the whole chain?
- Is the factor fixed, or a non-automatable setting applied in prepare?

## Sample-rate dependence

- Which values depend on the sample rate: filter coefficients, smoothing times, delay lengths, envelope rates, oversampling filters?
- Are they all computed from the rate passed to prepare, never hard-coded?
- The MPC is fixed at 44.1 kHz; desktop hosts run from 44.1 to 192 kHz. Does the design hold up across that whole range, including delay buffer sizes and CPU at 192 kHz?

## CPU budget

- What is the budget per target? On the 32-bit MPCs, aim for under 15% of a 128-frame block (about 0.4 ms) for the whole plugin, worst case.
- What are the expensive operations per sample (transcendental functions, divides, oversampled stages, voices)? Which can move to control rate or per block?
- Is the worst case bounded? For example, maximum voices, the longest delay, the highest oversampling factor.
- How will it be measured: `host_sim` timing for the MPC, a profiler or pluginval on the desktop?

## Portability between targets

- Which code lives in the portable core, and which in each wrapper?
- Does the core use only the standard library and get its sample rate and block size from the wrapper?
- Is smoothing done in one place, so every target sounds the same?

## Sources

- Adapted from the Plugin Freedom System's DSP architecture template (Taches, MIT), `.claude/skills/plugin-planning/assets/architecture-template.md`: its processing chain, parameter mapping, processing order and risk sections, reduced to questions with no document template.
- MPC facts: Akai MPC Plugin SDK `docs/host-contract.md` and `docs/dsp-cookbook.md` (commit e78bad5, 2026-11-23; MIT, copyright (c) 2026 inMusic Brands, Inc.).
