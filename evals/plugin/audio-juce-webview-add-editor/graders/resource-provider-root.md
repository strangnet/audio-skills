---
type: llm
focus: last_message
criteria: >
  The final message says to serve the page from inside the plugin through the WebBrowserComponent
  resource provider (withResourceProvider) and to load it with goToURL on
  getResourceProviderRoot(), not through a file:// URL, and says the root request reaches the
  provider as "/" (so "/" must map to index.html).
---
