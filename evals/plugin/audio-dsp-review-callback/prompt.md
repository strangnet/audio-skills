---
tags: [audio-dsp, trigger, advice]
max_turns: 20
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---
This saturator ships as a JUCE plugin (VST3, AU, CLAP) and as an Akai MPC plugin, with the DSP in `core/`. Review the audio callbacks (`juce/PluginProcessor.cpp` and `mpc/src/Saturator.cpp`) and the core code they call. Don't change any files yet: tell me what's wrong or risky for real-time audio on both targets, and what I should do about it.
