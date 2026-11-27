---
type: llm
focus: trace
criteria: >
  The agent treats the working folder as the SDK checkout and plugins/Grit/ as a project inside it,
  the case Akai's own skills and the SDK's AGENTS.md cover. It works from the SDK's own material
  (AGENTS.md, the README, the skills under .claude/skills/ or .agents/skills/, the tools in tools/)
  and runs the SDK's tools on plugins/Grit as the SDK intends. It doesn't apply advice meant for a
  project kept outside the SDK: it doesn't ask where the SDK is, doesn't tell the user to set
  MPC_SDK, and doesn't suggest moving the project out of plugins/. This holds whether or not the
  agent loaded the audio-mpc skill; if it did, it says Akai's skills lead inside a checkout and
  follows them.
---
