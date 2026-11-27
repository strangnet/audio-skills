---
type: llm
focus: last_message
criteria: >
  The final message says the editor's members must be declared in the order relays, then the
  WebBrowserComponent, then the attachments (or equivalently: each relay before the browser so it
  outlives it, and each attachment after its relay). It does not claim std::unique_ptr members
  are required.
---
