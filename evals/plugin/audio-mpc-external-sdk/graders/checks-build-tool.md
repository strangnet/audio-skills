---
type: llm
focus: trace
criteria: >
  Before the first command that runs the SDK's build tool, the agent checks that the folder the
  user named (mpc-sdk) holds the SDK's build tool, tools/build.py: for example by listing
  mpc-sdk/tools, testing that mpc-sdk/tools/build.py exists, or reading that file. Running
  build.py first and only then discovering whether it exists does not count.
---
