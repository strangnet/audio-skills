---
type: llm
focus: last_message
criteria: >
  The final message recommends denormal protection, for example adding juce::ScopedNoDenormals
  to processBlock (which has none), relying on the MPC SDK framework's flush-to-zero, or letting
  the core's decaying state reach zero.
---
