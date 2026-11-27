# 05: Akai's skills lead inside a checkout, and the package is complete

Status: ready
Spec: [mpc](../../mpc.md)
Blocked by: 02, 03, 04

## Delivers
The Inside a checkout eval case (a new scaffold whose tools folder holds a stub build tool), the desktop-only no-fire case, and the shared Claude Code and Cowork plugin cases re-checked with all six skills. The eval README's case table lists every new case. The spec's remaining inspections pass: no repeats of sibling skills beyond the four allowed rules, no Akai workflow, every fact and tool invocation cited at the pinned commit, and the `$MPC_SDK` rule stated.

## Scenarios
- inside an SDK checkout, on a project in its plugins folder → `audio-mpc` doesn't fire, and Akai's skills apply
- a desktop-only plugin → `audio-mpc` doesn't fire
- Claude Code or Cowork plugins → no `audio-*` skill fires
