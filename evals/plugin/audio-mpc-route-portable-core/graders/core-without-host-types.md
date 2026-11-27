---
type: llm
focus: last_message
criteria: >
  The final message says to move the chorus DSP out of process() into a header-only C++17 core
  that uses only the standard library and never sees host types (no mpc::ProcessContext,
  mpc::Plugin or juce:: types): each wrapper converts its host's buffers into plain float pointers
  with channel and frame counts, and its parameters into plain values.
---
