// Tilt EQ: the MPC wrapper around the portable core in ../../core.
//
// Parameter order is fixed and shared with the JUCE wrapper:
//   0  Output  dB trim, default 0 dB. It's at index 0 because the MPC nudges
//              parameter 0 to 1.0 or 0.0 and straight back on every prepare
//              (SDK docs/host-contract.md). A smoothed trim that defaults to
//              unity makes that nudge inaudible, and parameterChanged does nothing.
//   1  Tilt    dB, -12..+12, the core's one control.

#include "mpc_plugin.h"

#include "../../core/tilt_eq.h"

#include <algorithm>
#include <cmath>

namespace {

enum ParamIndex { kOutput = 0, kTilt, kNumParams };

constexpr int kMaxChannels = 2;
constexpr double kTrimSmoothingSeconds = 0.020;

float dbToGain(float db) { return std::pow(10.0f, db / 20.0f); }

}  // namespace

class TiltEq : public mpc::Plugin {
public:
    TiltEq() : mpc::Plugin(makeInfo()) {
        addParam(mpc::floatParam("output", "Output", -12.0f, 12.0f, 0.0f, "dB", 1));
        addParam(mpc::floatParam("tilt", "Tilt", -12.0f, 12.0f, 0.0f, "dB", 1));
    }

    void prepare(double sampleRate, int /*maxBlockSize*/) override {
        eq_.prepare(sampleRate);
        trimCoeff_ = static_cast<float>(std::exp(std::log(0.01) / (kTrimSmoothingSeconds * sampleRate)));
        reset();
    }

    void reset() override {
        eq_.setTilt(get(kTilt));
        trimGain_ = dbToGain(get(kOutput));
    }

    void process(mpc::ProcessContext& ctx) override {
        const int numChannels = std::min({ctx.numOutputs, ctx.numInputs, kMaxChannels});
        const int numFrames = ctx.numFrames;

        // The core works in place on the outputs. The host usually passes the same
        // buffers for inputs and outputs; copy only when it doesn't.
        for (int ch = 0; ch < numChannels; ++ch) {
            if (ctx.inputs[ch] != ctx.outputs[ch]) {
                std::copy(ctx.inputs[ch], ctx.inputs[ch] + numFrames, ctx.outputs[ch]);
            }
        }

        eq_.setTilt(get(kTilt));
        eq_.process(ctx.outputs, numChannels, numFrames);

        const float targetGain = dbToGain(get(kOutput));
        for (int i = 0; i < numFrames; ++i) {
            trimGain_ = targetGain + trimCoeff_ * (trimGain_ - targetGain);
            for (int ch = 0; ch < numChannels; ++ch) {
                ctx.outputs[ch][i] *= trimGain_;
            }
        }
    }

private:
    static mpc::PluginInfo makeInfo() {
        mpc::PluginInfo info;
        info.name = "Tilt EQ";
        info.vendor = "strangnet";  // must match plugin.json "manufacturer"
        info.uniqueId = MPC_FOURCC('S', 't', 'T', 'l');  // must match plugin.json "uid"
        info.version = 100;  // 0.1.0
        info.isInstrument = false;
        info.numInputs = 2;
        info.numOutputs = 2;
        info.tailSamples = 1;  // no tail
        return info;
    }

    tilt::TiltEq eq_;
    float trimGain_ = 1.0f;
    float trimCoeff_ = 0.0f;
};

MPC_PLUGIN_ENTRY(TiltEq)
