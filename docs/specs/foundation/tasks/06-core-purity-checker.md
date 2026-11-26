# 06: The core-purity checker proves a core is pure, and the script runs it on the example

Status: done
Spec: [foundation](../../foundation.md)
Blocked by: 02

## Delivers
The core-purity checker uses the shared checker interface: Python 3 using only the standard library, output lines of `file:line: severity: rule: message`, and exit codes 0, 1 and 2. It ships in the `audio-portable-core` skill folder, with pytest fixtures in CI. The example check script runs it on the core.

## Scenarios
- Core-purity: a clean core → no findings, success
- Core-purity: a JUCE include, a `juce::` name or a `JUCE_` macro → reported, failure (even without an include)
- Core-purity: an SDK include or an `mpc::` name → reported, failure
- Core-purity: a non-standard third-party include → reported, failure
- Core-purity: a `.cpp` file in the core → reported as not header-only, failure
- Core-purity: `juce::` only in a comment or string literal → not reported
- Core-purity: a missing path or no headers → usage message, usage-error code
- Example: the core passes the core-purity checker
