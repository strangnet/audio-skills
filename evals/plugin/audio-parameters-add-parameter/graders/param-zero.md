---
type: llm
focus: last_message
criteria: >
  The final message says parameter 0 (out_gain) must stay harmless because the MPC host nudges
  parameter 0 on load or prepare, so mix must not go at index 0 and nothing at index 0 should
  move.
---
