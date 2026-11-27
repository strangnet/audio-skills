---
type: llm
focus: last_message
criteria: >
  The final message says the build would also download and install zig into the SDK's tool cache
  (which needs network access) unless a zig is already on PATH, named by the ZIG environment
  variable, or passed with --zig. It is enough to name these three ways of avoiding the download;
  mentioning an existing zig install in the SDK is optional.
---
