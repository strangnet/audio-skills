# Denormals, smoothing, aliasing, latency and block sizes

JUCE facts are checked against JUCE 9.0.6. MPC facts are in [mpc-audio.md](mpc-audio.md).

## Denormals

A float decaying toward zero (a filter's state after the input stops, a reverb tail, a feedback delay) passes through the subnormal range, below about 1.2e-38. On many CPUs, arithmetic on subnormals is 10 to 100 times slower, so a plugin can spike in CPU during silence.

- **In the wrapper:** turn on flush-to-zero for the duration of the callback. JUCE: `juce::ScopedNoDenormals noDenormals;` as the first line of `processBlock` (declared in `juce_audio_basics/buffers/juce_FloatVectorOperations.h`). The MPC SDK framework does this around every `process()` on every CPU; see [mpc-audio.md](mpc-audio.md).
- **In the core:** don't rely on the wrapper. Flush recursive state to exact zero once it falls below an inaudible floor:

  ```cpp
  low = (1.0f - coeff) * x + coeff * low;
  if (std::fabs(low) < 1e-15f) low = 0.0f;  // about -300 dB
  ```

  Flush-to-zero only removes true subnormals. State between 1e-38 and 1e-30 is still slow on some chips, and the MPC's `host_sim` warns at |x| < 1e-30. Letting the state reach exact zero fixes both.
- Feedback loops with gain at or above 1 don't decay at all: clamp the feedback below 1 or put a soft clipper in the loop.

## Parameter smoothing

A parameter that jumps from one value to another between blocks makes a step in the signal: a click for gain, zipper noise for a sweeping cutoff.

- Read the parameter once per block, then move a smoothed copy toward it every sample. A one-pole smoother is `y = target + c * (y - target)`, with `c = exp(ln(0.01) / (seconds * sampleRate))` for 99% of the way in `seconds`.
- Pick the time per parameter: 10 to 20 ms for gains and mixes, 20 to 50 ms for filter frequencies. Smooth frequencies and gains in a perceptual domain (log frequency, dB), or the glide sounds lopsided.
- JUCE has `juce::SmoothedValue<float>` (linear) and `juce::SmoothedValue<float, juce::ValueSmoothingTypes::Multiplicative>` (for gains). Call `reset(sampleRate, seconds)` in `prepareToPlay` and `setTargetValue` per block.
- On prepare and reset, snap the smoothed value to the target so playback doesn't start with a glide.
- Put the smoother in one place. If the core smooths, the wrappers don't, so every target sounds the same.
- Parameters that can't be smoothed (a mode switch, a filter type) should crossfade between the old and new paths, or change only at a zero crossing.

## Aliasing and oversampling

A digital system can't represent frequencies above Nyquist (half the sample rate). Anything generated above it folds back down as an inharmonic tone.

- **Linear processing** (gain, EQ, linear filters, delays without modulation) creates no new frequencies and doesn't alias. Don't oversample it.
- **Nonlinear processing** (saturation, distortion, waveshaping, hard clipping, compression with a fast attack) creates harmonics. The harder the curve, the higher the harmonics. Oversample by 2x to 8x around the nonlinear stage only: upsample, process, filter and downsample.
- **Oscillators:** naive saw and square waves alias badly. Use band-limited methods (PolyBLEP, wavetables, BLIT) instead of oversampling.
- The MPC runs at 44.1 kHz, so Nyquist is 22.05 kHz and aliasing is closer to the audible band than at 96 kHz. Its CPU budget also limits oversampling, which is a reason to prefer gentle curves and band-limited methods there.
- JUCE: `juce::dsp::Oversampling<float>` (`juce_dsp/processors/juce_Oversampling.h`). Construct it outside the callback, call `initProcessing(maxBlockSize)` in `prepareToPlay`, and report `getLatencyInSamples()` as latency (below).
- Changing the oversampling factor reallocates and changes latency. Make it a non-automatable parameter and apply it in prepare, not in the callback.

## Latency reporting

If the output is delayed relative to the input, the host must know by how much, or the track drifts out of time with everything else.

- Things that add latency: oversampling filters, lookahead (limiters, compressors), FFT block processing, linear-phase filters, and any deliberate block-based delay.
- Report it in samples at the current sample rate. JUCE: `setLatencySamples(n)` (`juce_AudioProcessor.h`, in the `juce_audio_processors_headless` module in 9.0.6), from `prepareToPlay` or the constructor. MPC SDK: `PluginInfo::latencySamples`, or `setLatency(n)` after construction.
- Report a latency that is constant for a given setting. If a setting changes latency, report the new value when the setting changes, outside the audio callback. Hosts may restart playback to apply it.
- Report the plugin's tail too, if it rings on after the input stops (reverbs, delays), so hosts don't cut it off. JUCE: `getTailLengthSeconds()`. MPC SDK: `PluginInfo::tailSamples`.

## Block sizes

- The block size given to prepare is the **maximum**. Calls can be smaller, and some hosts vary the size from call to call, sometimes down to a single frame for automation or looping.
- Loop to `numFrames` (`buffer.getNumSamples()` in JUCE), never to the prepared size.
- Size scratch buffers for the maximum, or process long blocks in fixed chunks (for example 64 frames) from a fixed-size array.
- Algorithms that need a fixed block (FFT, block-based convolution) must buffer internally and report the resulting latency.
- Per-block work (reading parameters, computing coefficients) costs relatively more on small blocks. At 32 frames it runs four times as often as at 128.

## Sources

- JUCE 9.0.6 source: `juce_FloatVectorOperations.h` (`ScopedNoDenormals`), `juce_SmoothedValue.h`, `juce_Oversampling.h` (`getLatencyInSamples`), `juce_audio_processors_headless/processors/juce_AudioProcessor.h` (`setLatencySamples`).
- Akai MPC Plugin SDK (commit e78bad5, 2026-11-23): `framework/mpc_plugin.h` (`ScopedDenormalsOff`, `PluginInfo::latencySamples`, `tailSamples`, `setLatency`), `tools/host-sim/README.md` (denormal warning at |x| < 1e-30). MIT, copyright (c) 2026 inMusic Brands, Inc. Paraphrased.
