---
type: llm
focus: trace
criteria: >
  The agent applies the fix from the SDK's troubleshooting document (mpc-sdk/docs/troubleshooting.md,
  "MPC-E117"): it adds a "#define MPC_MAX_PARAMS <N>" line, with N at least 36 (the document
  suggests 64), to the plugin's own source my-plugin/src/StepGate.cpp, above its
  '#include "mpc_plugin.h"' line, and then rebuilds with the SDK's build tool and the build succeeds.
  Removing parameters from the plugin instead does not count.
---
