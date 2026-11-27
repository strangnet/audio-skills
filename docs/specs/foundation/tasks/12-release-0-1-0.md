# 12: The package is released at 0.1.0 and installable in every agent

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 04, 05, 09, 10, 11

## Delivers
- A README with every skill, install commands for each agent, the CI and eval commands, and Credits for the Plugin Freedom System and Akai's SDK.
- The Akai notice next to any long quote.
- The `strangnet` marketplace entry in `agent-skills`, with no version. **Ask first** before editing that repo.
- The release checklist run by hand: installs, a name-collision check, invoking a skill, and the manual M2 and M4 run, with notes for later specs.

## Scenarios
- Install: Claude Code from the `strangnet` marketplace → the skills are listed and invoking one by name loads it
- Install: Copilot CLI from the same marketplace → the skills are available
- Install: Codex from this repo's marketplace → the skills are available
- Install: pi or skills.sh from git → each skill folder is found on its own
- Install: `strangnet-skills` installed too → no skill names collide
- Reader: the README lists the skills, install commands, CI and eval commands, and Credits
- Reader: a long quote of Akai's material carries Akai's MIT notice
