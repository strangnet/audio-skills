---
tags: [audio-mpc, routing, audio-portable-core]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---
My MPC chorus, Swirl, is in `mpc/` in my own repo, outside Akai's SDK, and I build it with the SDK's tools from here. I'm about to add a desktop version with JUCE (VST3, AU, CLAP) in `juce/`, and I want both to share one DSP implementation instead of copying the chorus code. Don't change any files yet: tell me how to structure the code so the MPC wrapper and the JUCE wrapper use the same DSP.
