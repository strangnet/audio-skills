---
type: llm
focus: last_message
criteria: >
  The final message says each wrapper includes the core by a relative path from its own source
  folder (for example #include "../../core/..." from mpc/src/), because the MPC SDK's build
  compiles and includes only the project's src/ folder, and that the core must not be copied into
  mpc/src/.
---
