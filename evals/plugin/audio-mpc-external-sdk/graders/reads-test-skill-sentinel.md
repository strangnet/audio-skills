---
type: llm
focus: trace
criteria: >
  The agent reads Akai's stand-in test skill as a file by its path inside the SDK
  (mpc-sdk/.claude/skills/mpc-plugin-test/SKILL.md or mpc-sdk/.agents/skills/mpc-plugin-test/SKILL.md),
  and applies its pass condition: the host simulator's report must also contain the line
  "PASS  Q-Link sweep: all 16 knobs".
---
