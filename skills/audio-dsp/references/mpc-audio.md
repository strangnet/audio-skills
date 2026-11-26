# MPC audio facts

The MPC runs plugins on its own hardware through its own VST 2.4 host. These are the facts that shape DSP for it. They are paraphrased from Akai's MPC Plugin SDK (see Sources). When working inside an SDK checkout, Akai's own `mpc-plugin-dsp` skill and the SDK docs are the authority.

## The host's audio contract

| Fact | Consequence |
|---|---|
| **Sample rate is fixed at 44,100 Hz.** | Nyquist is 22.05 kHz. Still compute every coefficient from the sample rate passed to prepare, so the same core is right on the desktop. |
| **The announced block size is at least 128, but calls deliver 32, 64, 96, 128, 192, 256 or 512 frames**, as chosen in the MPC's preferences. A 32-frame setting still announces 128. | Treat the announced size as a maximum. Loop to `ctx.numFrames`. |
| **Inputs and outputs are usually the same buffers** (in-place). The framework clears only output channels that don't alias an input. | Read a frame's inputs before writing its outputs. Never clear the outputs before reading the inputs. A core that processes in place fits naturally: copy inputs to outputs only when the pointers differ. |
| Prepare repeats on sample-rate or block-size changes and after suspend and resume, and nudges parameter 0 each time. | Prepare must be idempotent. Parameter 0 must be harmless (see the `audio-parameters` skill). |
| Effects receive no MIDI. | Anything an effect needs must be a parameter. |
| The host reads latency (`initialDelay`) while loading the plugin. | Set `PluginInfo::latencySamples` in the constructor. `setLatency(n)` notifies the host with `audioMasterIOChanged`; prefer a latency that is fixed at load. |

## CPU budget

The MPC's CPU also runs its own sequencer, sampler and mixer, and the 32-bit models are the slowest.

| Models | CPU |
|---|---|
| MPC X, Live, One (32-bit) | Cortex-A17, the tightest budget |
| MPC Live II, One+, Key 61, X SE, 3 (64-bit) | Cortex-A55 or A76 |

- A 128-frame block at 44.1 kHz is 2.9 ms. The SDK's guidance for the A17 is **under 15% of the block, about 0.4 ms, for the whole plugin, worst case**.
- Rough A17 costs: `sin`, `tan`, `pow` or `exp` about 50 to 100 ns; a divide 10 to 20 ns; a multiply-add about 1 ns. Compute transcendental functions at control rate (every 16 to 32 samples) or once per block, not per sample, and use fast approximations where accuracy allows.
- Oversampling multiplies the cost of everything inside it. 4x oversampling of a heavy stage can use the whole budget.
- `host_sim` prints timing for the desktop build. The SDK says to multiply desktop times by roughly 15 to 25 for the A17. Treat it as orientation and test on the device.

## Denormals on the MPC

- The SDK framework turns flush-to-zero on around every `process()` call on every CPU (`ScopedDenormalsOff` in `framework/mpc_plugin.h`). The 64-bit MPCs' host doesn't do it for you, so a plugin outside the framework must do it itself.
- `host_sim` still warns about samples with 0 < |x| < 1e-30 during its silence pass. These are above the subnormal range, so flush-to-zero doesn't remove them. The fix is in the DSP: let decaying state reach exact zero (see [dsp-quality.md](dsp-quality.md)).

## Checking on the desktop

The SDK's `host_sim` loads the native build the way the MPC does and reports PASS, WARN and FAIL lines. It checks block sizes 32 and 512, in-place processing, the parameter 0 nudge, random parameter sweeps, state round-trips, NaN and Inf, clipping, denormals and timing. A FAIL means the MPC would reject the plugin, crash or produce broken audio.

## Sources

All from the Akai MPC Plugin SDK, version 1.0 plus the "Unreleased (will become 1.1)" changes in `docs/changelog.md` (checked at commit e78bad5, 2026-11-23). MIT licence, copyright (c) 2026 inMusic Brands, Inc. Paraphrased; no long quotes.

- `docs/host-contract.md`: sample rate, block sizes, load and prepare sequence, latency read at load.
- `docs/dsp-cookbook.md`, section 1: in-place processing (rule 4), smoothing (rule 6), denormals (rule 7), CPU budget and cost model (rule 8).
- `framework/mpc_plugin.h`: `ProcessContext` (in-place note), `ScopedDenormalsOff`, `PluginInfo::latencySamples`, `setLatency`.
- `tools/host-sim/README.md`: what `host_sim test` checks, the denormal threshold, timing as orientation.
- `tools/build.py`: the 32-bit and 64-bit model lists.
