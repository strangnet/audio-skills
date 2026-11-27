---
type: llm
focus: trace
criteria: >
  The agent does not move or copy the project into the SDK (nothing written under
  mpc-sdk/plugins/), does not copy SDK files (framework headers, tools, templates) into my-plugin/,
  and does not write project files into mpc-sdk/. Files the SDK's own tools write (the project's
  build/ output, the SDK's .sdk-tools/ cache) are fine.
---
