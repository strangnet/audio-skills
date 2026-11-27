---
tags: [audio-juce, trigger, instrument]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---
I'm writing a polyphonic synth as a JUCE 9 plugin (VST3, AU and CLAP through clap-juce-extensions, built with CMake). I started from my delay effect's project. What do I need to change in `juce_add_plugin`, the CLAP call and the `AudioProcessor` so hosts treat it as an instrument and send it MIDI? Answer in a short list.
