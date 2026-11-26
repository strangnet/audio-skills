# 08: The real-time checker handles markers, inline bodies, stripping, opt-outs and warnings

Status: done
Spec: [foundation](../../foundation.md)
Blocked by: 07

## Delivers
The real-time checker covers the edge cases. It scans core functions that carry the marker, scans an inline body without running on into later functions, and ignores comments, strings and helper `process` methods. It also supports the opt-out marker with a required reason, a `--verbose` option, and the denormal warning, which on its own still exits 0.

## Marker forms
Both markers are plain `//` comments that need no header, and share the `realtime` tag:
- **Real-time marker:** `// realtime`, alone on the line before the function (template or return-type lines may sit between). It makes the checker scan that function's body. The core's real-time entry points carry it.
- **Opt-out marker:** a trailing `// realtime-ok: <reason>` on the flagged line. It suppresses the findings on that line, and `--verbose` lists each one as `file:line: suppressed: rule: message (reason: ...)`. A tag with no reason suppresses nothing and is itself an `error` with rule `opt-out`.

The denormal warning has rule `denormal`. Protection means `juce::ScopedNoDenormals`, `FloatVectorOperations::disableDenormalisedNumberSupport`, or the `_MM_SET_FLUSH_ZERO_MODE`/`_MM_SET_DENORMALS_ZERO_MODE` macros inside the `processBlock` body.

## Scenarios
- Real-time: a core function with the real-time marker that breaks a rule → reported
- Real-time: a `processBlock` with no denormal protection → `warning`; warnings alone exit with success
- Real-time: an allocation outside every real-time body → not reported
- Real-time: an inline `processBlock` followed by a constructor that allocates → only `processBlock` scanned
- Real-time: a forbidden word only in a comment or string literal → not reported
- Real-time: a helper `process` method without `ProcessContext` and without the marker → not scanned
- Real-time: an opt-out marker with a reason → suppressed, and listed with its reason in verbose mode
- Real-time: an opt-out marker with no reason → the marker is reported as an error
