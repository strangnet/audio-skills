---
tags: [audio-mpc, routing, audio-dsp]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---
`my-plugin/` is my MPC echo effect, kept in my own repo outside Akai's SDK. On my MPC One it crackles when the audio buffer setting is 32, and it eats more CPU than I expected. Review the audio callback, `process()` in `my-plugin/src/Echo.cpp`. Don't change any files yet: tell me what's wrong for real-time audio on the MPC and how to fix it.
