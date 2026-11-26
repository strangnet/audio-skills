"""Real-time checker: finds processBlock and process(ProcessContext&) bodies by
matching braces and reports allocation, locks, I/O and logging inside them."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "audio-dsp" / "scripts" / "check_realtime.py"
EXAMPLE_CHECK = REPO / "examples" / "tilt-eq" / "check.py"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def run_check(*paths):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)], capture_output=True, text=True
    )


# Zero


CLEAN_JUCE = """\
#include "PluginProcessor.h"

void TiltEqAudioProcessor::prepareToPlay (double sampleRate, int samplesPerBlock)
{
    core.prepare (sampleRate);
}

void TiltEqAudioProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                         juce::MidiBuffer& midiMessages)
{
    juce::ignoreUnused (midiMessages);
    juce::ScopedNoDenormals noDenormals;
    core.setTilt (tilt->load());
    for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
    {
        auto* data = buffer.getWritePointer (ch);
        for (int i = 0; i < buffer.getNumSamples(); ++i)
            data[i] *= gain;
    }
}
"""


def test_clean_processblock_reports_nothing_and_succeeds(tmp_path):
    # Given a JUCE wrapper source whose processBlock body is clean
    source = write(tmp_path / "PluginProcessor.cpp", CLEAN_JUCE)

    # When the real-time checker runs on it
    result = run_check(source)

    # Then it reports no findings and exits with success
    assert result.returncode == 0, result.stdout + result.stderr
    assert ": error:" not in result.stdout
    assert ": warning:" not in result.stdout


def test_file_with_no_realtime_body_says_so_and_succeeds(tmp_path):
    # Given a source file that allocates but has no real-time body, only a
    # declaration of processBlock and a call to a helper process()
    source = write(
        tmp_path / "PluginProcessor.h",
        "class P {\n"
        "public:\n"
        "    P() { buffer.resize (1024); }\n"
        "    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;\n"
        "    void tick() { smoother.process(); }\n"
        "    std::vector<float> buffer;\n"
        "};\n",
    )

    # When the real-time checker runs on it
    result = run_check(source)

    # Then it says it found no real-time body and exits with success
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{source}: no real-time body found" in result.stdout
    assert ": error:" not in result.stdout


# One


MPC_WRAPPER = """\
#include "mpc_plugin.h"
#include "../../core/tilt_eq.h"

class TiltEqPlugin : public mpc::Plugin
{
public:
    void process(mpc::ProcessContext& ctx) override
    {
        core_.setTilt(tilt_.process());
        history_.push_back(ctx.outputs[0][0]);
        for (int i = 0; i < ctx.numFrames; ++i)
        {
            ctx.outputs[0][i] = ctx.inputs[0][i];
        }
    }

private:
    tilt::TiltEq core_;
    std::vector<float> history_;
};
"""


def test_mpc_process_with_processcontext_breaking_a_rule_is_reported(tmp_path):
    # Given an MPC wrapper whose process(ProcessContext&) grows a container on line 10
    source = write(tmp_path / "src" / "TiltEqPlugin.cpp", MPC_WRAPPER)

    # When the real-time checker runs on it
    result = run_check(source)

    # Then it reports that line with severity error and the allocation rule, and fails
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"{source}:10: error: allocation: " in result.stdout
    assert result.stdout.count(": error:") == 1


# Many


RULE_BREAKS = [
    ("auto* tmp = new float[512];", "allocation"),
    ("delete[] tmp;", "allocation"),
    ("void* raw = malloc (64);", "allocation"),
    ("free (raw);", "allocation"),
    ("events.push_back (e);", "allocation"),
    ("events.emplace_back (e);", "allocation"),
    ("scratch.resize (n);", "allocation"),
    ("scratch.reserve (n);", "allocation"),
    ("names.insert (name);", "allocation"),
    ("std::mutex m;", "lock"),
    ("std::lock_guard<std::mutex> guard (stateMutex);", "lock"),
    ("std::unique_lock<std::mutex> held (stateMutex);", "lock"),
    ("std::scoped_lock both (a, b);", "lock"),
    ('FILE* f = fopen ("/tmp/dump.raw", "wb");', "io"),
    ("fwrite (data, sizeof (float), n, f);", "io"),
    ('std::ofstream out ("dump.txt");', "io"),
    ('auto dump = juce::File ("/tmp/dump.wav");', "io"),
    ("juce::FileOutputStream stream (dump);", "io"),
    ('juce::URL url ("https://example.com");', "io"),
    ("int sock = socket (AF_INET, SOCK_STREAM, 0);", "io"),
    ('std::cout << "block";', "logging"),
    ('std::cerr << "block";', "logging"),
    ('printf ("%d", n);', "logging"),
    ('fprintf (stderr, "%d", n);', "logging"),
    ('DBG ("block " << n);', "logging"),
    ('juce::Logger::writeToLog ("block");', "logging"),
]


def test_each_rule_break_in_processblock_is_reported_as_an_error(tmp_path):
    # Given a processBlock with one rule break per line, starting on line 4
    first_line = 4
    body = "\n".join(f"    {code}" for code, _ in RULE_BREAKS)
    source = write(
        tmp_path / "PluginProcessor.cpp",
        "void P::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)\n"
        "{\n"
        "    juce::ScopedNoDenormals noDenormals;\n"
        f"{body}\n"
        "}\n",
    )

    # When the real-time checker runs on it
    result = run_check(source)

    # Then each break is reported with its file:line, severity error and rule,
    # and the checker fails
    assert result.returncode == 1, result.stdout + result.stderr
    for offset, (code, rule) in enumerate(RULE_BREAKS):
        expected = f"{source}:{first_line + offset}: error: {rule}: "
        assert expected in result.stdout, f"missing {expected!r} for {code!r}\n{result.stdout}"


# Interface


def load_example_check():
    spec = importlib.util.spec_from_file_location("example_check", EXAMPLE_CHECK)
    assert spec is not None and spec.loader is not None, f"cannot load {EXAMPLE_CHECK}"
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve postponed annotations through sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_example_core_and_wrappers_pass_the_realtime_check():
    # Given the example check script's real-time safety check
    example = load_example_check()
    checks = {check.name: check for check in example.CHECKS}
    assert "real-time safety" in checks

    # When it runs on the example's core and whichever wrappers exist
    ok, detail = checks["real-time safety"].run()

    # Then it passes
    assert ok, detail


# Exceptions


@pytest.mark.parametrize("args", [["missing.cpp"], []], ids=["missing-path", "no-path"])
def test_bad_path_prints_usage_and_exits_with_usage_error(tmp_path, args):
    # Given a path that doesn't exist, or no path at all
    paths = [tmp_path / arg for arg in args]

    # When the real-time checker runs
    result = run_check(*paths)

    # Then it prints usage and exits with the usage-error code
    assert result.returncode == 2, result.stdout + result.stderr
    assert "usage:" in result.stderr
    assert "Traceback" not in result.stderr
