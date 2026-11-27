# 06: audio-juce holds the JUCE 9 plugin know-how

Status: ready
Spec: [juce](../../juce.md)
Blocked by: 01

## Delivers
The `audio-juce` skill and its references: CMake, plugin codes, CLAP through clap-juce-extensions, bus layouts for effects and instruments, parameters, threading, the editor's lifecycle, programs and stale bundles, every fact checked against JUCE 9.0.6. Its eval cases, the shared "not for Claude Code or Cowork plugins" cases re-run with all five skills, and the README Skills and evals tables.

## Scenarios
- JUCE know-how: fires on setting up or fixing a JUCE plugin project, and its advice covers every listed item
- JUCE know-how: a WebView editor prompt → leaves the details to `audio-juce-webview`
- JUCE know-how: a Component-based editor → says it isn't covered, no Component advice
- JUCE know-how: an instrument → synth flag, MIDI input, output-only buses, and the listed-as-effect pitfall
- JUCE know-how: inside an Akai SDK checkout on an MPC-only plugin → doesn't fire
- JUCE know-how: another plugin framework (iPlug2, nih-plug) → doesn't fire
- Testing: the shared Claude Code and Cowork plugin cases keep passing
- Inspection: version-sensitive statements cite JUCE 9.0.6; no repeat of `audio-parameters` or `audio-dsp` beyond the allowed API line
