#pragma once

#include <array>
#include <cmath>

namespace tilt {

// The plugin's parameters, defined once. Both wrappers build their parameter lists
// from this table: JUCE keys them by `id`, the MPC addresses them by index. Ids are
// stable forever, and rows are only ever appended. Row 0 is harmless, because the
// MPC host nudges parameter 0 on every prepare.
struct ParamInfo {
    const char* id;
    const char* name;
    float min;
    float max;
    float def;
    const char* unit;
};

enum Param { kOutput = 0, kTilt, kNumParams };

inline constexpr std::array<ParamInfo, kNumParams> kParams{{
    {"output", "Output", -12.0f, 12.0f, 0.0f, "dB"},
    {"tilt", "Tilt", -12.0f, 12.0f, 0.0f, "dB"},
}};

class TiltEq {
public:
    void prepare(double sampleRate) {
        coeff_ = static_cast<float>(std::exp(-2.0 * kPi * kPivotHz / sampleRate));
        // One-pole smoother that covers 99% of a jump in kSmoothingSeconds.
        smoothCoeff_ = static_cast<float>(std::exp(std::log(0.01) / (kSmoothingSeconds * sampleRate)));
    }

    // Sets a parameter by its index in kParams, in plain units (dB).
    void setParam(int index, float plainValue) {
        if (index == kOutput) outputGain_ = std::pow(10.0f, plainValue / 20.0f);
        if (index == kTilt) setTilt(plainValue);
    }

    void setTilt(float db) { tiltDb_ = db; }

    float smoothedTilt() const { return smoothedDb_; }

    // realtime
    void process(float* const* channels, int numChannels, int numFrames) {
        for (int i = 0; i < numFrames; ++i) {
            smoothedDb_ = tiltDb_ + smoothCoeff_ * (smoothedDb_ - tiltDb_);
            smoothedGain_ = outputGain_ + smoothCoeff_ * (smoothedGain_ - outputGain_);
            const float highGain = std::pow(10.0f, smoothedDb_ / 40.0f);
            const float lowGain = 1.0f / highGain;
            for (int ch = 0; ch < numChannels && ch < kMaxChannels; ++ch) {
                const float x = channels[ch][i];
                float& low = lowState_[ch];
                low = (1.0f - coeff_) * x + coeff_ * low;
                // Flush the decaying state to zero before it reaches the denormal
                // range, where some CPUs (the MPC's ARM chips among them) slow down.
                if (std::fabs(low) < kDenormalFloor) low = 0.0f;
                channels[ch][i] = (low * lowGain + (x - low) * highGain) * smoothedGain_;
            }
        }
    }

private:
    static constexpr double kPi = 3.14159265358979323846;
    static constexpr double kPivotHz = 1000.0;
    static constexpr double kSmoothingSeconds = 0.020;
    static constexpr int kMaxChannels = 2;
    static constexpr float kDenormalFloor = 1e-15f;  // about -300 dB: inaudible

    float coeff_ = 0.0f;
    float smoothCoeff_ = 0.0f;
    float tiltDb_ = 0.0f;
    float smoothedDb_ = 0.0f;
    float outputGain_ = 1.0f;
    float smoothedGain_ = 1.0f;
    float lowState_[kMaxChannels] = {};
};

}  // namespace tilt
