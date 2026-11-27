---
type: llm
focus: last_message
criteria: >
  The final message says the build failed because it couldn't write into the SDK, and explains
  that a first build writes into the SDK clone: it compiles the host simulator into the SDK's tool
  cache (mpc-sdk/.sdk-tools/), so that run needs write access to the SDK folder.
---
