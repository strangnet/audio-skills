---
tags: [audio-juce, trigger, advice]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---
I have the DSP for a saturation effect in `core/grit.h`, with its parameter table. I want to wrap it as a JUCE 9 plugin in `juce/`, built with CMake on macOS, shipping VST3, AU and CLAP, with a custom editor that I'll write later. Don't write any files yet: tell me what the `CMakeLists.txt` and the `AudioProcessor` need to get right so the plugin builds, loads and behaves in every host the first time.
