---
type: llm
focus: last_message
criteria: >
  The final message recommends including JUCE module headers directly (such as
  juce_audio_processors/juce_audio_processors.h) rather than JuceHeader.h, or says JuceHeader.h
  is optional in a CMake project and only exists if juce_generate_juce_header is called.
---
