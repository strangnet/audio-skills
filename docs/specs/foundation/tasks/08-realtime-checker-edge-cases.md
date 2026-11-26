# 08: The real-time checker handles markers, inline bodies, stripping, opt-outs and warnings

Status: ready
Spec: [foundation](../../foundation.md)
Blocked by: 07

## Delivers
The real-time checker covers the edge cases. It scans core functions that carry the marker, scans an inline body without running on into later functions, and ignores comments, strings and helper `process` methods. It also supports the opt-out marker with a required reason, a `--verbose` option, and the denormal warning, which on its own still exits 0.

## Scenarios
- Real-time: a core function with the real-time marker that breaks a rule → reported
- Real-time: a `processBlock` with no denormal protection → `warning`; warnings alone exit with success
- Real-time: an allocation outside every real-time body → not reported
- Real-time: an inline `processBlock` followed by a constructor that allocates → only `processBlock` scanned
- Real-time: a forbidden word only in a comment or string literal → not reported
- Real-time: a helper `process` method without `ProcessContext` and without the marker → not scanned
- Real-time: an opt-out marker with a reason → suppressed, and listed with its reason in verbose mode
- Real-time: an opt-out marker with no reason → the marker is reported as an error
