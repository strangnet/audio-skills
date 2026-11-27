---
type: llm
focus: trace
criteria: >
  The agent reads Akai's stand-in deploy skill as a file by its path inside the SDK
  (mpc-sdk/.agents/skills/mpc-plugin-deploy/SKILL.md or mpc-sdk/.claude/skills/mpc-plugin-deploy/SKILL.md),
  and its sentinel appears in what the agent tells the user: the MPC-SAFE-COPY check, that is,
  checking the drive's VST2 Plugins folder for an older copy of the same plugin (same uid) before
  copying. Install steps the agent makes up without reading that file do not count.
---
