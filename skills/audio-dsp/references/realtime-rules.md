# Real-time rules and the checker

## Why the rules exist

The host calls the audio callback on a high-priority thread and needs the block back before the audio device asks for it. At 44.1 kHz a 128-frame block is 2.9 ms; at 32 frames it is 0.7 ms. An operation that is usually fast but can occasionally wait is the problem: the wait happens rarely, at random, and is heard as a click or dropout that is hard to reproduce.

## Never in real-time code

This applies to the callback and to everything it calls, including the DSP core.

| Category | Examples | Why it can wait |
|---|---|---|
| Allocation | `new`, `delete`, `malloc`, `calloc`, `realloc`, `free`; `push_back`, `emplace_back`, `resize`, `reserve`, `insert` on containers; building a `std::string`; `std::function` holding a large capture | The allocator can take a lock or ask the OS for memory. Freeing can be just as slow. |
| Locks | `std::mutex` and its variants, `lock_guard`, `unique_lock`, `scoped_lock`, `shared_lock`, `juce::CriticalSection` | Another thread may hold the lock, and it may be descheduled while it does (priority inversion). |
| Blocking I/O | `fopen`, `fread`, `fwrite`, streams, JUCE `File`, `FileInputStream`, `FileOutputStream`, `URL`, sockets | The disk or network can take any amount of time. |
| Logging | `printf`, `std::cout`, `DBG`, `juce::Logger`, `mpc::log` | Console and log output allocate, lock and do I/O. |
| Unbounded work | waiting on a condition, spinning on another thread, loops whose length depends on something other than the block size | The block's cost has no upper bound. |

## What to do instead

- Allocate and size everything in prepare: buffers, delay lines, FFT plans, oversamplers. Prepare runs before audio starts and again when the sample rate or maximum block size changes. Size for the largest block, not a typical one.
- Pass parameters to the audio thread as atomics, such as JUCE's `getRawParameterValue()` or the MPC SDK's `get(index)`. Read each one once per block.
- Pass larger data, such as a loaded sample or impulse response, by preparing it on another thread and swapping a pointer atomically. Free the old one off the audio thread.
- Send information out of the audio thread (meters, scopes) through lock-free FIFOs or atomics. A UI timer reads them.

## The checker

`scripts/check_realtime.py` reads source code only. It strips comments and string literals before matching, then scans each real-time body by matching braces.

**What it scans:**
- every function named `processBlock` (JUCE)
- every function named `process` that takes a `ProcessContext` (the Akai SDK's callback); a helper method named `process` with other parameters is not scanned
- every function with the **real-time marker** on the line before it:

  ```cpp
  // realtime
  void process(float* const* channels, int numChannels, int numFrames) {
  ```

  The marker is a `// realtime` comment alone on its line. Template or return-type lines may sit between it and the function name; a `;`, `{` or `}` in between cancels it. Put it on every core function the wrapper's callback calls.

**What it reports:**
- errors for the rules `allocation`, `lock`, `io` and `logging`
- a warning, rule `denormal`, when a `processBlock` contains none of `ScopedNoDenormals`, `disableDenormalisedNumberSupport`, `_MM_SET_FLUSH_ZERO_MODE` or `_MM_SET_DENORMALS_ZERO_MODE`. Warnings alone exit 0.

**Opting out of a finding.** A trailing comment on the flagged line suppresses that line's findings:

```cpp
scratch.resize(maxBlock); // realtime-ok: only runs when the host grows the block, before audio restarts
```

The reason after the colon is required; a bare `// realtime-ok` is itself an error. `--verbose` lists each suppressed finding with its reason, as `file:line: suppressed: rule: message (reason: ...)`. Use opt-outs rarely, and only with a reason a reviewer can check.

**What it can't see:**
- **It doesn't follow calls.** A clean callback that calls an allocating helper passes. Mark the helpers, or keep real-time code in marked functions.
- Allocation hidden behind an innocent-looking line: constructing a container with a size (`std::vector<float> tmp(numFrames);`), copying a `std::vector` or `std::string` by value, `juce::String` concatenation, `std::function` construction, a `std::map` lookup with `operator[]` that inserts, exceptions.
- Unbounded loops, waiting on atomics, and system calls not in its word list.
- Loggers outside its word list. It knows `cout`, `cerr`, `printf`, `fprintf`, `DBG` and `Logger`, but not the MPC SDK's `mpc::log` or a project's own logging macros.
- Code reached through virtual calls or function pointers.

A passing checker is the minimum. Review real-time code by hand as well, and measure with the platform's tools (pluginval at high strictness on desktop, `host_sim` timing for the MPC).

## Sources

- Rule list adapted from the Plugin Freedom System's real-time rules (Taches, MIT), `.claude/agents/dsp-agent.md`, "CRITICAL Real-Time Rules" and "Real-Time Safety Checklist". The list in this package's foundation spec is the one the checker implements.
- MPC rules: Akai MPC Plugin SDK `docs/dsp-cookbook.md` section 1 and `docs/host-contract.md` (commit e78bad5, 2026-11-23; MIT, copyright (c) 2026 inMusic Brands, Inc.). Paraphrased.
