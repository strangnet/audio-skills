# 13: Both checkers follow the amended checker interface

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 06, 07

## Delivers
The checkers follow the amendments made to the spec after tasks 06 and 07 were reviewed, and after tasks 08 and 10:
- both read `.hpp` as headers and `.cc` and `.cxx` as sources
- the core-purity checker warns on deprecated C headers and reports a sources-only core as header-only errors
- the real-time checker treats a folder with no source files as a usage error
- the real-time checker reports local standard containers and `mpc::log` in real-time bodies

## Scenarios
- Core-purity: a deprecated C header such as `<math.h>` → `warning` naming the replacement; warnings alone exit with success
- Core-purity: a core folder that holds only source files → header-only errors, not a usage error
- Core-purity: a missing path, or one with no headers or source files → usage message, usage-error code (now counting `.hpp`, `.cc` and `.cxx`)
- Real-time: a bad path, or a folder with no source files → usage message, usage-error code
- Real-time: a local standard container declared in a real-time body (`std::vector<float> gains(numFrames);`) → `allocation` error
- Real-time: `mpc::log` in a real-time body → `logging` error

The last two scenarios come from the second round of spec amendments (2026-11-27), which also wrote down three behaviours task 08 already has:
- the opt-out suppresses every finding on its line
- the marker may sit above template or return-type lines
- `--verbose` lines use `suppressed` in place of the severity

Those three need no code change. Their tests already exist from task 08.
