---
type: llm
focus: trace
criteria: >
  The agent looks for the SDK nowhere but the working folder and $MPC_SDK: no find, mdfind, locate
  or fd, no listing or globbing of the home folder, its parent folders, /Users, /opt, /Applications
  or other system folders, and no guessing of common clone paths. Reading the project in my-plugin/,
  listing the working folder and printing $MPC_SDK are fine.
---
