# 04: The example check script runs the binding checker

Status: ready
Spec: [juce](../../juce.md)
Blocked by: 01

## Delivers
The tilt-EQ check script runs the binding checker on the JUCE wrapper's editor and UI folder and lists it in its summary. A test asserts the check is in the script's check list.

## Scenarios
- Example: the binding checker passes on the JUCE wrapper, and the summary lists it as a check
- Example: every existing example check still passes
