# 03: The JUCE wrapper ships VST3, AU and CLAP and passes every validator

Status: done
Spec: [foundation](../../foundation.md)
Blocked by: 02

## Delivers
The example's JUCE wrapper:
- built with JUCE 9.0.6 plus clap-juce-extensions pinned to a tested commit
- a generic editor for now
- JUCE found through a CMake cache variable or an environment variable, never an absolute path

The example check script builds VST3, AU and CLAP and runs pluginval (strictness 10, VST3 and AU), clap-validator and auval. This tests assumption M3.

## Scenarios
- Example: the JUCE wrapper builds VST3, AU and CLAP
- Example: pluginval passes at strictness level 10 for VST3 and AU
- Example: clap-validator passes for the CLAP build
- Example: auval passes for the AU build
