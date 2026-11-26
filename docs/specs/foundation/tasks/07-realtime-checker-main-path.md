# 07: The real-time checker catches rule breaks in audio callbacks, and the script runs it

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 02

## Delivers
The main path of the real-time checker:
- finds `processBlock` and `process(ProcessContext&)` bodies by matching braces
- applies the full rule list from the spec
- uses the shared checker interface and exit codes

It ships in the `audio-dsp` skill folder, with pytest fixtures in CI. The example check script runs it on the core and on both wrappers.

## Scenarios
- Real-time: a clean `processBlock` → no findings, success
- Real-time: allocation, a lock, I/O or logging in a real-time body → each reported with `file:line`, severity `error` and the rule, failure
- Real-time: an MPC wrapper's `process(ProcessContext&)` breaking a rule → reported in the same way
- Real-time: a source file with no real-time body → says so, success
- Real-time: a bad path → usage message, usage-error code
- Example: the core and both wrappers pass the real-time checker
