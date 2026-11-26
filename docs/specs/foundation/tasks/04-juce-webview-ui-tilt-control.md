# 04: The JUCE wrapper has a WebView UI whose tilt control automates the parameter

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 03

## Delivers
The generic editor is replaced by a minimal WebView UI built on JUCE 9's in-source WebView interop. It has one tilt control bound to the tilt parameter, and moving it records automation in a DAW. The validators from task 03 still pass.

## Scenarios
- Example: manual DAW check (moving the WebView tilt control changes the parameter and is recorded as automation)
