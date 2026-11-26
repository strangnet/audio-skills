---
type: llm
focus: last_message
criteria: >
  The final message says the code must handle whatever block size the host delivers rather than
  assume one: for example it flags the fixed 128-sample scratch array in processBlock as unsafe
  for larger blocks, says the prepared block size is only a maximum, or notes that the MPC
  delivers 32 to 512 frames per call.
---
