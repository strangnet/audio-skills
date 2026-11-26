// Behaviour tests for the tilt-EQ core. Standard library only.
// Build and run: c++ -std=c++17 -O2 -o /tmp/core_test core_test.cpp && /tmp/core_test

#include "../core/tilt_eq.h"

#include <cmath>
#include <cstdio>
#include <random>
#include <string>
#include <vector>

namespace {

int failures = 0;

void check(bool ok, const char* test, const char* what) {
    if (!ok) {
        std::printf("FAIL %s: %s\n", test, what);
        ++failures;
    }
}

constexpr double kSampleRate = 44100.0;

double toDb(double ratio) { return 20.0 * std::log10(ratio); }

void zero_tilt_output_equals_input() {
    // Given a core at 0 dB tilt and a block of stereo noise
    tilt::TiltEq eq;
    eq.prepare(kSampleRate);
    eq.setTilt(0.0f);
    std::mt19937 rng(1);
    std::uniform_real_distribution<float> noise(-1.0f, 1.0f);
    std::vector<float> left(4096), right(4096);
    for (auto& s : left) s = noise(rng);
    for (auto& s : right) s = noise(rng);
    const std::vector<float> inLeft = left, inRight = right;
    float* channels[] = {left.data(), right.data()};

    // When the block is processed
    eq.process(channels, 2, 4096);

    // Then the output equals the input to within -90 dB
    double maxError = 0.0;
    for (size_t i = 0; i < left.size(); ++i) {
        maxError = std::fmax(maxError, std::fabs(left[i] - inLeft[i]));
        maxError = std::fmax(maxError, std::fabs(right[i] - inRight[i]));
    }
    check(maxError == 0.0 || toDb(maxError) < -90.0, __func__, "output differs from input");
}

// Steady-state gain in dB of a sine at `hz` through a core at `tiltDb`,
// measured over the last half of one second so smoothing has settled.
double sineGainDb(double hz, float tiltDb) {
    tilt::TiltEq eq;
    eq.prepare(kSampleRate);
    eq.setTilt(tiltDb);
    const int n = static_cast<int>(kSampleRate);
    std::vector<float> buffer(n);
    for (int i = 0; i < n; ++i)
        buffer[i] = static_cast<float>(0.5 * std::sin(2.0 * M_PI * hz * i / kSampleRate));
    const std::vector<float> input = buffer;
    float* channels[] = {buffer.data()};
    eq.process(channels, 1, n);
    double inEnergy = 0.0, outEnergy = 0.0;
    for (int i = n / 2; i < n; ++i) {
        inEnergy += input[i] * input[i];
        outEnergy += buffer[i] * buffer[i];
    }
    return 10.0 * std::log10(outEnergy / inEnergy);
}

void positive_tilt_raises_highs_and_lowers_lows() {
    // Given a core tilted by +6 dB

    // When a 10 kHz and a 100 Hz sine pass through it
    const double highGain = sineGainDb(10000.0, 6.0f);
    const double lowGain = sineGainDb(100.0, 6.0f);

    // Then 10 kHz comes out louder and 100 Hz quieter
    check(highGain > 1.0, __func__, "10 kHz not raised by at least 1 dB");
    check(lowGain < -1.0, __func__, "100 Hz not lowered by at least 1 dB");
}

void negative_tilt_lowers_highs_and_raises_lows() {
    // Given a core tilted by -6 dB

    // When a 10 kHz and a 100 Hz sine pass through it
    const double highGain = sineGainDb(10000.0, -6.0f);
    const double lowGain = sineGainDb(100.0, -6.0f);

    // Then 10 kHz comes out quieter and 100 Hz louder
    check(highGain < -1.0, __func__, "10 kHz not lowered by at least 1 dB");
    check(lowGain > 1.0, __func__, "100 Hz not raised by at least 1 dB");
}

// Smoothed tilt after each frame, for `frames` frames after jumping from
// `fromDb` (already settled) to `toDb`.
std::vector<float> smoothedTrace(float fromDb, float toDb, int frames) {
    tilt::TiltEq eq;
    eq.prepare(kSampleRate);
    eq.setTilt(fromDb);
    float sample = 0.0f;
    float* channels[] = {&sample};
    for (int i = 0; i < static_cast<int>(kSampleRate); ++i) eq.process(channels, 1, 1);
    eq.setTilt(toDb);
    std::vector<float> trace;
    for (int i = 0; i < frames; ++i) {
        eq.process(channels, 1, 1);
        trace.push_back(eq.smoothedTilt());
    }
    return trace;
}

void smoothed_tilt_moves_monotonically_to_target() {
    // Given a core settled at -12 dB

    // When the tilt jumps to +12 dB and 100 ms are processed
    const std::vector<float> trace = smoothedTrace(-12.0f, 12.0f, 4410);

    // Then the smoothed tilt never moves backwards and ends at the target
    bool monotonic = true;
    for (size_t i = 1; i < trace.size(); ++i)
        if (trace[i] < trace[i - 1]) monotonic = false;
    check(monotonic, __func__, "smoothed tilt moved backwards");
    check(std::fabs(trace.back() - 12.0f) < 0.01f, __func__, "smoothed tilt did not reach the target");
}

void smoothed_tilt_settles_between_15_and_25_ms() {
    // Given a core settled at -12 dB

    // When the tilt jumps to +12 dB
    const std::vector<float> trace = smoothedTrace(-12.0f, 12.0f, 4410);

    // Then it first gets within 1% of the jump from the target between 15 and 25 ms
    const float tolerance = 0.01f * 24.0f;
    int settledAt = -1;
    for (size_t i = 0; i < trace.size(); ++i) {
        if (std::fabs(trace[i] - 12.0f) <= tolerance) {
            settledAt = static_cast<int>(i) + 1;
            break;
        }
    }
    const double ms = 1000.0 * settledAt / kSampleRate;
    check(ms >= 15.0 && ms <= 25.0, __func__, "did not settle between 15 and 25 ms");
}

void smoothed_tilt_never_moves_more_than_1_percent_per_sample() {
    // Given a core settled at -12 dB

    // When the tilt jumps to +12 dB
    const std::vector<float> trace = smoothedTrace(-12.0f, 12.0f, 4410);

    // Then no single sample moves the smoothed tilt by more than 1% of the jump
    float largestStep = trace.front() - (-12.0f);
    for (size_t i = 1; i < trace.size(); ++i)
        largestStep = std::fmax(largestStep, std::fabs(trace[i] - trace[i - 1]));
    check(largestStep <= 0.01f * 24.0f, __func__, "a single sample moved more than 1% of the jump");
}

void parameter_table_defines_output_then_tilt() {
    // Given the core's parameter table, the one definition both wrappers use

    // Then it holds Output at index 0, harmless at its 0 dB default, then Tilt
    check(tilt::kNumParams == 2, __func__, "expected two parameters");
    check(std::string(tilt::kParams[tilt::kOutput].id) == "output", __func__, "index 0 is not output");
    check(tilt::kOutput == 0, __func__, "output is not parameter 0");
    check(tilt::kParams[tilt::kOutput].def == 0.0f, __func__, "output default is not 0 dB");
    check(std::string(tilt::kParams[tilt::kTilt].id) == "tilt", __func__, "index 1 is not tilt");
}

void output_trim_scales_the_signal_once_settled() {
    // Given a core at 0 dB tilt and +6 dB output, set through the parameter interface
    tilt::TiltEq eq;
    eq.prepare(kSampleRate);
    eq.setParam(tilt::kTilt, 0.0f);
    eq.setParam(tilt::kOutput, 6.0f);
    const int n = static_cast<int>(kSampleRate);
    std::vector<float> buffer(n, 0.25f);
    float* channels[] = {buffer.data()};

    // When one second of a constant signal is processed
    eq.process(channels, 1, n);

    // Then the settled output is about twice the input (+6.02 dB)
    check(std::fabs(buffer.back() / 0.25f - std::pow(10.0f, 6.0f / 20.0f)) < 1e-3f, __func__,
          "settled output is not +6 dB");
    check(buffer.front() < 0.26f, __func__, "output jumped instead of gliding");
}

void silence_after_signal_leaves_no_denormals() {
    // Given a tilted core that has just processed a loud low sine
    tilt::TiltEq eq;
    eq.prepare(kSampleRate);
    eq.setTilt(6.0f);
    const int n = static_cast<int>(kSampleRate);
    std::vector<float> buffer(n);
    for (int i = 0; i < n / 10; ++i)
        buffer[i] = static_cast<float>(0.9 * std::sin(2.0 * M_PI * 100.0 * i / kSampleRate));
    float* channels[] = {buffer.data()};
    eq.process(channels, 1, n / 10);

    // When two seconds of silence follow
    std::vector<float> silence(2 * n, 0.0f);
    float* silent[] = {silence.data()};
    eq.process(silent, 1, 2 * n);

    // Then no output sample is a tiny nonzero value (host_sim's denormal threshold,
    // which also covers every true subnormal): the filter state decays to exact zero
    bool tiny = false;
    for (float s : silence)
        if (s != 0.0f && std::fabs(s) < 1e-30f) tiny = true;
    check(!tiny, __func__, "silence produced denormal-range samples");
}

}  // namespace

int main() {
    zero_tilt_output_equals_input();
    positive_tilt_raises_highs_and_lowers_lows();
    negative_tilt_lowers_highs_and_raises_lows();
    smoothed_tilt_moves_monotonically_to_target();
    smoothed_tilt_settles_between_15_and_25_ms();
    smoothed_tilt_never_moves_more_than_1_percent_per_sample();
    silence_after_signal_leaves_no_denormals();
    parameter_table_defines_output_then_tilt();
    output_trim_scales_the_signal_once_settled();
    if (failures == 0) std::printf("all core tests passed\n");
    return failures == 0 ? 0 : 1;
}
