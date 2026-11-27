---
type: llm
focus: last_message
criteria: >
  For the reset button and the meter, the final message says native function (and event)
  callbacks run on the message thread, and that events to the page (emitEventIfBrowserIsVisible)
  should be sent from the message thread, for example from a timer, only after the page has first
  finished loading, never from the audio thread.
---
