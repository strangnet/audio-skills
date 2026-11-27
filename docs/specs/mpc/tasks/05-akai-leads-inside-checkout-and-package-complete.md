# 05: Akai's skills lead inside a checkout, and the package is complete

Status: done
Spec: [mpc](../../mpc.md)
Blocked by: 02, 03, 04

## Delivers
The Inside a checkout eval case (a new scaffold whose tools folder holds a stub build tool), the desktop-only no-fire case, and the shared Claude Code and Cowork plugin cases re-checked with all six skills. The eval README's case table lists every new case. The spec's remaining inspections pass: no repeats of sibling skills beyond the four allowed rules, no Akai workflow, every fact and tool invocation cited at the pinned commit, and the `$MPC_SDK` rule stated.

## Scenarios
- inside an SDK checkout, on a project in its plugins folder → `audio-mpc` doesn't fire, and Akai's skills apply
- a desktop-only plugin → `audio-mpc` doesn't fire
- Claude Code or Cowork plugins → no `audio-*` skill fires

## Notes

- New cases: `audio-mpc-inside-checkout` (the working folder is itself a stand-in checkout, made by `stand_in_sdk .`, with the project in `plugins/Grit/`) and `audio-mpc-desktop-only`. Both "doesn't fire" graders set `arm: both`, and so do the shared Claude Code and Cowork cases now. Their `audio-[\w-]+` pattern already covers all six skills.
- The stand-in SDK gained a stub `tools/mpc_remote.py` with the real tool's usage text and argument forms. It never connects, and every device command fails with "can't reach the MPC". The stand-in `mpc-plugin-deploy` skill now names its network route, so the install cases test the real temptation.
- The No SDK grader stays narrower than the spec's first wording: `find` counts only outside the working folder. The spec now says so.
- Inspections passed: the `$MPC_SDK` rule is in `SKILL.md`; each fact cites its SDK file at `e78bad5`, and the tool invocations match the argument parsers of `build.py`, `validate.py`, `package.py` and `new_plugin.py` and the host simulator's README; nothing repeats a sibling skill beyond the four one-line rules; Akai's workflow appears only as something to leave out; there are no install steps; the tilt-EQ MPC wrapper keeps every hard rule; the map was corrected in `de0ad17`; and the README's Skills table lists `audio-mpc` with no "planned".
- Not run: the 14 `audio-mpc-*` eval cases and the two shared cases. They cost money and were deferred. The spec stays `approved` until they pass.
