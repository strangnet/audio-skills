---
type: llm
focus: last_message
criteria: >
  The final message identifies that goToURL(getResourceProviderRoot()) makes the resource
  provider receive the path "/" for the page, which this provider (stripping the slash and
  matching only "index.html") doesn't answer, so the page request gets nothing; and it says to
  map "/" to index.html.
---
