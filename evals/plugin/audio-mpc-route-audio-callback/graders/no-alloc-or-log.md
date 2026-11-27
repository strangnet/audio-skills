---
type: llm
focus: last_message
criteria: >
  The final message says process() must not allocate (the std::vector created per block) or log
  (the printf per block), and suggests allocating in prepare and removing the logging.
---
