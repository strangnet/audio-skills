---
type: llm
focus: last_message
criteria: >
  The final message warns that a state name (or type) the C++ side doesn't know fails silently:
  it only logs a console warning (such as "unknown to the backend") and the control stays
  frozen.
---
