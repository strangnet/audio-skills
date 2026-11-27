---
type: llm
focus: last_message
criteria: >
  The final message says the per-sample std::pow for the output gain wastes CPU on the MPC's slow
  ARM processor, and that it should be computed once per block (or at control rate), with the gain
  smoothed so changes don't click.
---
