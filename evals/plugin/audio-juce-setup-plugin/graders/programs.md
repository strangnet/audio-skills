---
type: llm
focus: last_message
criteria: >
  The final message says getNumPrograms() must return at least 1, and that setCurrentProgram
  should be a no-op for a plugin without programs, because some hosts call it after restoring
  state.
---
