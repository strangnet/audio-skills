---
type: llm
focus: last_message
criteria: >
  The final message says processBlock should read parameters through the raw-value atomics from
  getRawParameterValue, with the pointers cached once (for example in the constructor) rather
  than looked up by string on every block.
---
