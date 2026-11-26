---
type: llm
focus: last_message
criteria: >
  The final message says each wrapper should include the core by a relative path from its own
  source folder (for example #include "../../core/..." from the MPC project's src/), and gives
  the reason that the MPC SDK build compiles and includes only the project's src/ folder, so the
  core can't simply be added to an include path.
---
