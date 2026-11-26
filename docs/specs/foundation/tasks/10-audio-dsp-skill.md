# 10: audio-dsp gives real-time and architecture know-how

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 08

## Delivers
The `audio-dsp` skill: a `SKILL.md` plus references, alongside the real-time checker it already holds. The references cover:
- the real-time rules, including the limit that the checker doesn't follow calls
- denormals, smoothing, aliasing and oversampling, and latency
- the MPC's block sizes, sample rate and CPU budget, with their sources
- the DSP architecture checklist

It comes with eval cases.

## Scenarios
- DSP: an audio-callback prompt → fires, with every advice item
- DSP: a plan-the-DSP prompt → offers the architecture checklist
- DSP: the same prompt → no planning steps, step order or templates
- DSP: an offline WAV converter prompt → doesn't fire
