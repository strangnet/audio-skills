# 05: The MPC wrapper builds from the same core and passes host_sim

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 02

## Delivers
The example's MPC wrapper is a standard SDK effect project whose `src/` includes the core by relative path. The example check script:
- finds zig itself
- calls the SDK's build tool with absolute paths, `--toolchain zig` and `--zig`
- builds for arm32 and arm64, including the SDK's validation step
- checks the Knob FX mapping in the manifest
- runs `host_sim`
- checks that exactly one copy of each core header exists and that both wrappers' includes resolve to it

This completes assumption M1.

## Scenarios
- Example: the MPC wrapper builds for arm32 and arm64 through the SDK's build tool, including its validation step
- Example: the MPC manifest declares a Knob FX mapping
- Example: `host_sim` reports no FAIL
- Example: exactly one copy of each core header exists, both wrappers' includes resolve to those files, and no build modifies them
- Example: the MPC wrapper's parameter 0 is harmless (code inspection)
- Example: manual MPC check (it loads on an MPC; the Q-Link changes the sound)
