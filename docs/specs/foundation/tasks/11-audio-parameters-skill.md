# 11: audio-parameters gives parameter, state and preset know-how

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 01

## Delivers
The `audio-parameters` skill: a `SKILL.md` plus references, with eval cases. The references cover:
- the parameter spec format
- the MPC parameter constraints and Knob FX, with sources
- how to version and migrate saved state
- presets that reference parameters by id

## Scenarios
- Parameters: an add-or-change-parameter prompt → fires, with every advice item
- Parameters: removing or renaming a released parameter → keep the old id and migrate saved state
- Parameters: a Claude Code plugin settings or CLI parameters prompt → doesn't fire
