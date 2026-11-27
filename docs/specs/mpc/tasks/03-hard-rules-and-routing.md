# 03: The MPC's hard rules and routing to sibling skills

Status: ready
Spec: [mpc](../../mpc.md)
Blocked by: 01

## Delivers
The skill's hard-rule summary, including the four one-line rules it shares with `audio-parameters`, each citing its SDK source at the pinned commit, and its topic-to-document table. The New effect eval case and three routing cases are written. An inspection confirms the tilt-EQ MPC wrapper keeps every rule the skill states.

## Scenarios
- when `audio-mpc` fires, its advice covers every hard-rule item
- an audio-callback question on the MPC → `audio-dsp`, named not repeated
- a parameter, Knob FX, MPC Sample or preset question on the MPC → `audio-parameters`, with only the four one-line rules in `audio-mpc`
- sharing DSP between the MPC wrapper and a JUCE wrapper → `audio-portable-core`
