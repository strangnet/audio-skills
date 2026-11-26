#pragma once

#include <cmath>

namespace tilt {

class TiltEq {
public:
    void prepare(double sampleRate) {
        coeff_ = static_cast<float>(std::exp(-2.0 * kPi * kPivotHz / sampleRate));
        // One-pole smoother that covers 99% of a jump in kSmoothingSeconds.
        smoothCoeff_ = static_cast<float>(std::exp(std::log(0.01) / (kSmoothingSeconds * sampleRate)));
    }

    void setTilt(float db) { tiltDb_ = db; }

    float smoothedTilt() const { return smoothedDb_; }

    // realtime
    void process(float* const* channels, int numChannels, int numFrames) {
        for (int i = 0; i < numFrames; ++i) {
            smoothedDb_ = tiltDb_ + smoothCoeff_ * (smoothedDb_ - tiltDb_);
            const float highGain = std::pow(10.0f, smoothedDb_ / 40.0f);
            const float lowGain = 1.0f / highGain;
            for (int ch = 0; ch < numChannels && ch < kMaxChannels; ++ch) {
                const float x = channels[ch][i];
                float& low = lowState_[ch];
                low = (1.0f - coeff_) * x + coeff_ * low;
                // Flush the decaying state to zero before it reaches the denormal
                // range, where some CPUs (the MPC's ARM chips among them) slow down.
                if (std::fabs(low) < kDenormalFloor) low = 0.0f;
                channels[ch][i] = low * lowGain + (x - low) * highGain;
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
    float lowState_[kMaxChannels] = {};
};

}  // namespace tilt
