// Behaviour tests for the tilt-EQ core. Standard library only.
// Build and run: c++ -std=c++17 -O2 -o /tmp/core_test core_test.cpp && /tmp/core_test

#include "../core/tilt_eq.h"

#include <cmath>
#include <cstdio>
#include <random>
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

}  // namespace

int main() {
    zero_tilt_output_equals_input();
    positive_tilt_raises_highs_and_lowers_lows();
    negative_tilt_lowers_highs_and_raises_lows();
    smoothed_tilt_moves_monotonically_to_target();
    smoothed_tilt_settles_between_15_and_25_ms();
    smoothed_tilt_never_moves_more_than_1_percent_per_sample();
    if (failures == 0) std::printf("all core tests passed\n");
    return failures == 0 ? 0 : 1;
}
