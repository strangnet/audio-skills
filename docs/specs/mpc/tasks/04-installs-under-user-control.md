# 04: Installs stay under the user's control

Status: ready
Spec: [mpc](../../mpc.md)
Blocked by: 01

## Delivers
The skill states the install-consent rule, hands install steps to Akai's `mpc-plugin-deploy` read for facts, and rules out rooting, firmware changes, system-file edits and hand-written SSH or scp to the device. The Install asked and Install not asked eval cases are written on the stand-in SDK scaffold, with finished build output.

## Scenarios
- a build is done → the agent asks whether to install, and installs only after an explicit yes for that plugin and that MPC
- the user asks for an install → the steps come from `mpc-plugin-deploy`; `audio-mpc` gives none of its own
- any install route → no rooting, firmware patches, system-file edits or hand-written SSH or scp to the device
