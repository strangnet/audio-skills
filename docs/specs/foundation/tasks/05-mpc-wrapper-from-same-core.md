# 05: The MPC wrapper builds from the same core and passes host_sim

Status: done (manual MPC check skipped by the user on 2026-11-27; not yet run on hardware)
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

## Decisions
- Parameter 0 is `Output`, a dB trim from -12 to +12, default 0 dB, smoothed over 20 ms in the core. Tilt is parameter 1. Both wrappers build their parameters from the core's table (`tilt::kParams`). The MPC nudges parameter 0 to 1.0 or 0.0 and straight back on every prepare (SDK `docs/host-contract.md`). A smoothed trim at unity makes that nudge inaudible, and `parameterChanged` does nothing.
- Knob FX mapping: knob 1 is `Tilt`, knob 2 is `Output`.

## Manual MPC check
1. Run the example check with `MPC_SDK` set. Then copy `examples/tilt-eq/mpc/build/strangnet - VST - Tilt EQ/` into a folder named `VST2 Plugins` on the MPC's drive (SDK `docs/install-and-test.md`).
2. Load Tilt EQ as an insert effect on a track with audio.
3. Turn the first Q-Link, or Knob FX knob 1, labelled `Tilt`. Turning it right should brighten the sound and turning it left should darken it.
4. Turn knob 2, labelled `Output`. The level should change, with no clicks.

It passes when the plugin loads and both controls change the sound as described.
