# 04: The JUCE wrapper has a WebView UI whose tilt control automates the parameter

Status: done (manual DAW check passed 2026-11-27: Bitwig CLAP and VST3, Logic AU)
Spec: [foundation](../../foundation.md)
Blocked by: 03

## Delivers
The generic editor is replaced by a minimal WebView UI built on JUCE 9's in-source WebView interop. It has one tilt control bound to the tilt parameter, and moving it records automation in a DAW. The validators from task 03 still pass.

## Scenarios
- Example: manual DAW check (moving the WebView tilt control changes the parameter and is recorded as automation)

  Steps (Reaper; Live works the same way with its own automation lanes):
  1. Run `JUCE_DIR=/path/to/JUCE python3 examples/tilt-eq/check.py`, then copy `build/tilt-eq/juce/TiltEq_artefacts/Release/VST3/Tilt EQ.vst3` into `~/Library/Audio/Plug-Ins/VST3`. The check already installs the AU. Rescan plugins in the DAW.
  2. Put "Tilt EQ" on a track with audio and open its UI. Expect a dark window with a "Tilt" slider and a readout of `0.00 dB`.
  3. Drag the slider. The readout follows, the sound tilts, and the DAW's own parameter view for Tilt (Reaper: the FX window's "Param" menu or the track's envelope list) shows the same value.
  4. Arm automation for the track (Reaper: automation mode "Touch" or "Write"; Live: Arm Automation), play, and drag the slider for a few seconds. Stop. An automation lane for Tilt holds the recorded moves.
  5. Set automation to "Read" and play again. The WebView slider and readout move with the recorded automation.
  6. Use the keyboard on the focused slider (arrow keys) while recording. Each key press is recorded too.

  Pass when steps 3 to 5 all hold for VST3 and AU (and CLAP, if the DAW loads it).
