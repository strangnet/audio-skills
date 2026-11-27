---
type: llm
focus: last_message
criteria: >
  The final message identifies that the page calls setNormalisedValue without sliderDragStarted()
  and sliderDragEnded(), so the cutoff edits reach the parameter outside any change gesture and
  the host doesn't record them; and it says to call sliderDragStarted() when the user starts an
  edit and sliderDragEnded() when it ends (for example on pointer release or the input's change
  event).
---
