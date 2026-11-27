---
type: llm
focus: last_message
criteria: >
  The final message says process() wrongly assumes 128 frames per call (the fixed wetBlock array
  and the loops to 128): the MPC delivers 32 to 512 frames per call depending on its buffer
  setting, so the code must loop to ctx.numFrames and treat the announced block size as a
  maximum.
---
