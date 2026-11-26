# 13: Both checkers follow the amended checker interface

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 06, 07

## Delivers
The checkers follow the amendments made to the spec after tasks 06 and 07 were reviewed:
- both read `.hpp` as headers and `.cc` and `.cxx` as sources
- the core-purity checker warns on deprecated C headers and reports a sources-only core as header-only errors
- the real-time checker treats a folder with no source files as a usage error

## Scenarios
- Core-purity: a deprecated C header such as `<math.h>` → `warning` naming the replacement; warnings alone exit with success
- Core-purity: a core folder that holds only source files → header-only errors, not a usage error
- Core-purity: a missing path, or one with no headers or source files → usage message, usage-error code (now counting `.hpp`, `.cc` and `.cxx`)
- Real-time: a bad path, or a folder with no source files → usage message, usage-error code

## Proposed, needs a spec amendment first
Found while writing the `audio-dsp` skill (task 10), and not yet in the spec:
- The `logging` rule doesn't catch the MPC SDK's own `mpc::log`, which the SDK's DSP cookbook allows only on the constructor or UI thread.
- The `allocation` rule doesn't catch a container constructed with a size, such as `std::vector<float> gains(numFrames);` inside a marked core function. The task 10 eval run found it.
- Task 08 differs from the spec's wording in three places:
  - An opt-out suppresses every finding on its line, not only one finding.
  - The marker may sit above template or return-type lines.
  - `--verbose` prints `suppressed` where the spec's format allows only `error` or `warning`.
