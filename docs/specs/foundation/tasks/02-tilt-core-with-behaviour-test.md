# 02: The tilt-EQ core is proven by its behaviour test, run by the example check script

Status: done
Spec: [foundation](../../foundation.md)
Blocked by: 01

## Delivers
- **The core:** the example's header-only tilt-EQ core, with 20 ms one-pole smoothing, the smoothed value exposed for testing, and the real-time marker on `process`.
- **The behaviour test:** a standalone C++17 program that uses only the standard library.
- **The example check script, first version:** it runs the behaviour test and works out pass, fail or incomplete, skipping checks whose tool is missing.

## Scenarios
- Example: the core's behaviour test passes (identity at 0 dB tilt to within −90 dB; tilt raises and lowers 10 kHz and 100 Hz in the right direction; smoothing is monotonic, within 1% of the target between 15 ms and 25 ms, and no single-sample move above 1% of the jump)
- Example: a required tool is missing → only the checks that need it are skipped, the script says what's missing and where to get it, and nothing is installed
- Example: a check fails → every check that doesn't depend on it still runs, and every failed and skipped check is listed
- Example: overall outcome precedence (fail, then incomplete, then pass; a check skipped because a check it depends on failed counts toward fail)
