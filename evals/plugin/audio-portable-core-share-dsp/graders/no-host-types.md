---
type: llm
focus: last_message
criteria: >
  The final message says the core must not see host types such as juce::AudioBuffer,
  juce::dsp::ProcessSpec or mpc::ProcessContext: each wrapper converts host buffers into plain
  float pointers with channel and frame counts, parameters into plain values, and passes the
  sample rate.
---
