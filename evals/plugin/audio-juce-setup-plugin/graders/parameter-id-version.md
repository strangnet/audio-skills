---
type: llm
focus: last_message
criteria: >
  The final message says to create the parameters with juce::ParameterID carrying a version hint
  (for example ParameterID { id, 1 }), mentions that the hint affects AU parameter ordering, and
  says to build the parameter layout from the core's parameter table (kParams) rather than
  listing parameters by hand.
---
