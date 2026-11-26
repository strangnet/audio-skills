// Tilt EQ: the MPC wrapper around the portable core in ../../core.
//
// The parameters, their ids and their order come from the core's table
// (tilt::kParams), shared with the JUCE wrapper. Index 0 is Output, a trim that
// defaults to 0 dB and is smoothed in the core: the MPC nudges parameter 0 to 1.0
// or 0.0 and straight back on every prepare (SDK docs/host-contract.md), and that
// nudge is inaudible. parameterChanged does nothing. The Knob FX mapping in
// plugin.json refers to these indices.

#include "mpc_plugin.h"

#include "../../core/tilt_eq.h"

#include <algorithm>

namespace {

constexpr int kMaxChannels = 2;
constexpr int kDisplayDecimals = 1;

}  // namespace

class TiltEq : public mpc::Plugin {
public:
    TiltEq() : mpc::Plugin(makeInfo()) {
        for (const tilt::ParamInfo& p : tilt::kParams) {
            addParam(mpc::floatParam(p.id, p.name, p.min, p.max, p.def, p.unit, kDisplayDecimals));
        }
    }

    void prepare(double sampleRate, int /*maxBlockSize*/) override {
        eq_.prepare(sampleRate);
        pushParams();
    }

    void reset() override { pushParams(); }

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

        pushParams();
        eq_.process(ctx.outputs, numChannels, numFrames);
    }

private:
    // Reads each parameter once and hands it to the core in plain units.
    void pushParams() {
        for (int i = 0; i < tilt::kNumParams; ++i) eq_.setParam(i, get(i));
    }

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
};

MPC_PLUGIN_ENTRY(TiltEq)
