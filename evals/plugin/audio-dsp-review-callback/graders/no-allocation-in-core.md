---
type: llm
focus: last_message
criteria: >
  The final message says the audio callback must not allocate, lock, do blocking I/O or log, and
  applies this to the core code the callback calls: it flags the std::vector created inside the
  core's process() as an allocation on the audio thread, and the mpc::log call in the MPC
  process().
---
