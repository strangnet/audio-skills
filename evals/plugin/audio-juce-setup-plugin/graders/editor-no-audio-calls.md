---
type: llm
focus: last_message
criteria: >
  The final message says the editor must never call into the audio callback or run the DSP
  directly, and should talk to the audio thread only through parameters, atomics or a lock-free
  FIFO.
---
