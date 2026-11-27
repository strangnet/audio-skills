---
type: llm
focus: trace
criteria: >
  The commands the agent runs call the SDK's tools by absolute path (for example
  python3 /…/mpc-sdk/tools/build.py, not tools/build.py run from inside mpc-sdk) and pass the
  project folder as an absolute path in the real argument forms: build.py and validate.py take the
  project folder (or, for validate.py, the built plugin folder) as a positional argument, with no
  --dir. A cd into mpc-sdk followed by relative paths fails this check.
---
