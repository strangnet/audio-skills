---
type: llm
focus: last_message
criteria: >
  The final message says the page must load JUCE's library as an ES module (script
  type="module") and import the state functions from it (for example
  import * as Juce from "./juce/index.js"), rather than reaching them through window.__JUCE__.
---
