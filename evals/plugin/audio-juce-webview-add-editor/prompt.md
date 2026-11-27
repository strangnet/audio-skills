---
tags: [audio-juce-webview, trigger, advice]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---
My JUCE 9 distortion plugin in this folder has no editor yet. I want a WebView editor on macOS: an HTML page embedded in the plugin with a knob for `drive`, a button for `bypass` and a dropdown for `mode`, a "reset" button that calls a C++ function, and later a level meter fed from the processor. Don't write any files yet: tell me what the C++ editor, the CMake setup and the page's JavaScript need to get right so the controls work and automation records the first time.
