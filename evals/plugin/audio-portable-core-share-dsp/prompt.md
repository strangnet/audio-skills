---
tags: [audio-portable-core, trigger, advice]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---
I have a JUCE compressor plugin in `juce/`. I now want to ship the same compressor as an Akai MPC plugin too, built with Akai's MPC Plugin SDK, and share one DSP implementation between the two instead of writing it twice. Don't change any files yet: tell me how to structure the code so both plugins use the same DSP.
