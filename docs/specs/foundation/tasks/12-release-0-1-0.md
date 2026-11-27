# 12: The package is released at 0.1.0 and installable in every agent

Status: in progress (Codex, Copilot and the M2/M4 run remain)
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

## Release checklist (2026-11-27)

- Claude Code: installed from the `strangnet` marketplace (agent-skills 0.8.0). A fresh session lists `audio-dsp`, `audio-parameters` and `audio-portable-core`, and invoking `audio-portable-core` by name loads it. Passed.
- Name collisions: `strangnet-skills` is installed alongside; it has no `audio-*` skill, and the fresh session lists only the three. Passed.
- pi: `pi install git:github.com/strangnet/audio-skills -l` in a scratch project; pi lists all three skills. Passed.
- skills.sh: `npx skills@latest add strangnet/audio-skills --list` finds all three skill folders. Passed.
- Codex: not checked; Codex isn't installed on the release machine.
- Copilot CLI: not checked; Copilot isn't installed on the release machine.
- M2 and M4 manual run: not yet done.
- MPC hardware: the manual MPC check from task 05 was skipped and hasn't been run on hardware. Deferred by the user (2026-11-27) to a later stage, once they have access to the hardware; it doesn't block closing this task.
