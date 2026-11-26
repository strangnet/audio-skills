---
type: llm
focus: last_message
criteria: >
  The final message says not to delete tone from the middle of the parameter list or renumber
  the parameters after it: tone keeps its id and its index slot (for example as an inert,
  hidden, non-automatable parameter), or its id is retired and never reused, so mix and every
  later parameter keep their indices.
---
