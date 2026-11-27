# 02: SDK edge cases: none found, first build, a changed SDK, test failures and fixes

Status: done
Spec: [mpc](../../mpc.md)
Blocked by: 01

## Delivers
The skill covers an SDK that isn't found (ask, never search or clone unasked), no SDK at all (how to get it), builds that write into the SDK and need write or network access, and the SDK's documents winning over the skill's summary. The No SDK, First build, SDK changed, Test failure and Fix eval cases are written on the stand-in SDK scaffold.

## Scenarios
- `$MPC_SDK` unset, or naming a folder without the build tool → the agent asks where the SDK is
- no SDK exists → the hard rules are still stated, and the skill explains how to get the SDK
- the first build, or a build after an SDK update that changed the host simulator → the build writes into the SDK; a sandboxed agent hands that run to the user
- a fact in the skill's summary differs from the found SDK's document → the agent follows the SDK and says it has changed
- the agent calls an SDK tool: the host simulator's FAIL counts as a failed check, and a fix changes the project, not the SDK (the failure and fix parts of task 01's scenarios)
