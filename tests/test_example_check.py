"""Example check script: runs every check, skips checks whose tool is missing, and
reports pass, fail or incomplete. Tested with fake checks and a fake tool lookup."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "examples" / "tilt-eq" / "check.py"


def load_check_module():
    spec = importlib.util.spec_from_file_location("example_check", SCRIPT)
    assert spec is not None and spec.loader is not None, f"cannot load {SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve postponed annotations through sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def ex():
    return load_check_module()


def all_tools_present(_name):
    return True


# Zero


def test_no_checks_is_a_pass(ex):
    # Given no checks

    # When the checks run
    report = ex.run_checks([], find_tool=all_tools_present)

    # Then the outcome is pass with exit code 0
    assert report.outcome == "pass"
    assert report.exit_code == 0


# One


def test_one_passing_check_is_a_pass_with_a_summary_line(ex):
    # Given one check that passes
    checks = [ex.Check("core behaviour test", run=lambda: (True, ""))]

    # When the checks run
    report = ex.run_checks(checks, find_tool=all_tools_present)

    # Then the outcome is pass and the summary names the check as passed
    assert report.outcome == "pass"
    assert report.exit_code == 0
    assert "PASS  core behaviour test" in report.lines


def test_one_failing_check_is_a_fail(ex):
    # Given one check that fails
    checks = [ex.Check("auval", run=lambda: (False, "component not found"))]

    # When the checks run
    report = ex.run_checks(checks, find_tool=all_tools_present)

    # Then the outcome is fail with exit code 1, and the detail is shown
    assert report.outcome == "fail"
    assert report.exit_code == 1
    assert "FAIL  auval: component not found" in report.lines


def test_check_with_missing_tool_is_skipped_and_run_is_incomplete(ex):
    # Given a check that needs pluginval, which isn't installed
    ran = []
    pluginval = ex.Tool("pluginval", hint="https://github.com/Tracktion/pluginval/releases")
    checks = [ex.Check("pluginval VST3", run=lambda: ran.append(1) or (True, ""), tools=[pluginval])]

    # When the checks run
    report = ex.run_checks(checks, find_tool=lambda name: name != "pluginval")

    # Then the check is skipped, the missing tool and where to get it are named,
    # and the outcome is incomplete with exit code 2
    assert ran == []
    assert report.outcome == "incomplete"
    assert report.exit_code == 2
    assert (
        "SKIP  pluginval VST3: pluginval not found "
        "(get it from https://github.com/Tracktion/pluginval/releases)"
    ) in report.lines


# Many


def test_failing_check_does_not_stop_later_checks_and_all_failures_are_listed(ex):
    # Given a failing check, a passing check and another failing check
    checks = [
        ex.Check("pluginval VST3", run=lambda: (False, "crashed in editor test")),
        ex.Check("auval", run=lambda: (True, "")),
        ex.Check("clap-validator", run=lambda: (False, "state test failed")),
    ]

    # When the checks run
    report = ex.run_checks(checks, find_tool=all_tools_present)

    # Then every check ran and both failures are listed
    assert report.outcome == "fail"
    assert "FAIL  pluginval VST3: crashed in editor test" in report.lines
    assert "PASS  auval" in report.lines
    assert "FAIL  clap-validator: state test failed" in report.lines


def test_check_skipped_because_its_dependency_failed_counts_toward_fail(ex):
    # Given an MPC build that fails and host_sim, which depends on it
    ran = []
    checks = [
        ex.Check("MPC build", run=lambda: (False, "undefined symbol")),
        ex.Check(
            "host_sim", run=lambda: ran.append(1) or (True, ""), depends_on=["MPC build"]
        ),
    ]

    # When the checks run
    report = ex.run_checks(checks, find_tool=all_tools_present)

    # Then host_sim doesn't run, is listed as skipped because of the failure,
    # and the run is a fail rather than incomplete
    assert ran == []
    assert "SKIP  host_sim: depends on failed check MPC build" in report.lines
    assert report.outcome == "fail"
    assert report.exit_code == 1


def test_check_whose_dependency_was_skipped_for_a_missing_tool_is_skipped_too(ex):
    # Given an MPC build that needs zig, which is missing, and host_sim after it
    ran = []
    zig = ex.Tool("zig", hint="https://ziglang.org/download/")
    checks = [
        ex.Check("MPC build", run=lambda: (True, ""), tools=[zig]),
        ex.Check(
            "host_sim", run=lambda: ran.append(1) or (True, ""), depends_on=["MPC build"]
        ),
    ]

    # When the checks run
    report = ex.run_checks(checks, find_tool=lambda name: name != "zig")

    # Then host_sim doesn't run either, and the run is incomplete
    assert ran == []
    assert "SKIP  host_sim: depends on skipped check MPC build" in report.lines
    assert report.outcome == "incomplete"
    assert report.exit_code == 2


# Boundaries


def test_fail_and_incomplete_in_one_run_is_a_fail(ex):
    # Given one check skipped for a missing tool and one that fails
    pluginval = ex.Tool("pluginval", hint="https://github.com/Tracktion/pluginval/releases")
    checks = [
        ex.Check("pluginval VST3", run=lambda: (True, ""), tools=[pluginval]),
        ex.Check("auval", run=lambda: (False, "component not found")),
    ]

    # When the checks run
    report = ex.run_checks(checks, find_tool=lambda name: name != "pluginval")

    # Then fail wins over incomplete
    assert report.outcome == "fail"
    assert report.exit_code == 1


# Exceptions


def test_check_that_crashes_counts_as_failed_with_its_error_shown(ex):
    # Given a check that raises, followed by one that passes
    def crashes():
        raise FileNotFoundError("build/TiltEq.vst3")

    checks = [
        ex.Check("pluginval VST3", run=crashes),
        ex.Check("auval", run=lambda: (True, "")),
    ]

    # When the checks run
    report = ex.run_checks(checks, find_tool=all_tools_present)

    # Then the crash is a failure with its error shown, and later checks still run
    assert report.outcome == "fail"
    assert "FAIL  pluginval VST3: crashed: FileNotFoundError: build/TiltEq.vst3" in report.lines
    assert "PASS  auval" in report.lines


# --- WebView bindings (juce task 04) -------------------------------------------


def test_check_list_runs_the_binding_checker_on_the_juce_editor_and_ui(ex):
    # Given the example's check list

    # When the WebView binding check is looked up by name
    checks = {check.name: check for check in ex.CHECKS}

    # Then it is there, needs no tool or build, and points the binding checker
    # at the JUCE wrapper's editor sources and UI folder
    assert "WebView bindings" in checks
    binding = checks["WebView bindings"]
    assert binding.tools == [] and binding.depends_on == []
    assert ex.BINDING_CHECKER.is_file()
    assert ex.BINDING_FOLDERS == [ex.HERE / "juce" / "Source", ex.HERE / "juce" / "ui"]


def test_binding_check_passes_on_the_example_and_the_summary_lists_it(ex):
    # Given only the example's WebView binding check
    checks = [check for check in ex.CHECKS if check.name == "WebView bindings"]

    # When the checks run
    report = ex.run_checks(checks, find_tool=all_tools_present)

    # Then it passes and the summary lists it as a passed check
    assert report.lines == ["PASS  WebView bindings"]
    assert report.outcome == "pass"


# --- MPC wrapper (task 05) ---------------------------------------------------


# Finding zig and the SDK


def nothing_on_path(_name):
    return None


def test_zig_is_not_found_when_neither_zig_env_nor_path_has_it(ex):
    # Given no ZIG variable and no zig on PATH
    environ = {}

    # When the script looks for zig
    zig = ex.find_zig(environ, which=nothing_on_path)

    # Then it finds none
    assert zig is None


def test_zig_is_found_on_path(ex):
    # Given zig on PATH and no ZIG variable
    def which(name):
        return "/opt/homebrew/bin/zig" if name == "zig" else None

    # When the script looks for zig
    zig = ex.find_zig({}, which=which)

    # Then it finds the one on PATH
    assert zig == Path("/opt/homebrew/bin/zig")


def test_zig_env_wins_over_path(ex, tmp_path):
    # Given a ZIG variable naming a zig that exists, and another zig on PATH
    chosen = tmp_path / "zig"
    chosen.write_text("")

    # When the script looks for zig
    zig = ex.find_zig({"ZIG": str(chosen)}, which=lambda _name: "/opt/homebrew/bin/zig")

    # Then it picks the one ZIG names
    assert zig == chosen


def test_zig_env_pointing_at_a_missing_file_is_not_found(ex, tmp_path):
    # Given a ZIG variable naming a file that doesn't exist, and zig on PATH
    missing = tmp_path / "no-such-zig"

    # When the script looks for zig
    zig = ex.find_zig({"ZIG": str(missing)}, which=lambda _name: "/opt/homebrew/bin/zig")

    # Then it finds none, rather than quietly using a zig the user didn't choose
    assert zig is None


def fake_sdk(root):
    (root / "tools").mkdir(parents=True)
    (root / "tools" / "build.py").write_text("")
    return root


def test_mpc_sdk_is_found_when_mpc_sdk_env_holds_the_build_tool(ex, tmp_path):
    # Given MPC_SDK naming a folder with tools/build.py
    sdk = fake_sdk(tmp_path / "sdk")

    # When the script looks for the SDK
    found = ex.find_mpc_sdk({"MPC_SDK": str(sdk)})

    # Then it finds that folder
    assert found == sdk


@pytest.mark.parametrize("environ_for", [
    lambda tmp: {},
    lambda tmp: {"MPC_SDK": ""},
    lambda tmp: {"MPC_SDK": str(tmp / "missing")},
    lambda tmp: {"MPC_SDK": str(tmp)},  # exists, but has no tools/build.py
], ids=["unset", "empty", "missing folder", "not an SDK"])
def test_mpc_sdk_is_not_found_when_mpc_sdk_env_is_unset_or_wrong(ex, tmp_path, environ_for):
    # Given MPC_SDK that is unset, empty, missing or not an SDK checkout
    environ = environ_for(tmp_path)

    # When the script looks for the SDK
    found = ex.find_mpc_sdk(environ)

    # Then it finds none
    assert found is None


# Calling the SDK's build tool


def test_build_command_uses_absolute_paths_the_zig_toolchain_and_the_found_zig(ex, tmp_path, monkeypatch):
    # Given the SDK, the project and zig named by relative paths
    monkeypatch.chdir(tmp_path)

    # When the script builds the command for the SDK's build tool
    command = ex.mpc_build_command(
        sdk=Path("sdk"), project=Path("mpc"), zig=Path("bin/zig"), python="/usr/bin/python3"
    )

    # Then every path is absolute, both ARM targets are built, and zig is the one found
    assert command == [
        "/usr/bin/python3", str(tmp_path / "sdk" / "tools" / "build.py"), str(tmp_path / "mpc"),
        "--target", "all", "--toolchain", "zig", "--zig", str(tmp_path / "bin" / "zig"),
    ]


# Knob FX mapping


def test_manifest_with_no_knob_mapping_is_a_problem(ex):
    # Given a manifest with no knobs and no shiftKnobs
    manifest = {"name": "Tilt EQ"}

    # When the script checks its Knob FX mapping
    problems = ex.knob_fx_problems(manifest, num_params=2)

    # Then it says the mapping is missing
    assert problems == ["plugin.json has no Knob FX mapping (knobs or shiftKnobs)"]


def test_manifest_with_one_labelled_knob_on_a_real_parameter_is_fine(ex):
    # Given one knob, labelled, on parameter 1 of 2
    manifest = {"knobs": [{"parameter": 1, "label": "Tilt"}], "shiftKnobs": []}

    # When the script checks its Knob FX mapping
    problems = ex.knob_fx_problems(manifest, num_params=2)

    # Then there are no problems
    assert problems == []


def test_shift_knobs_alone_count_as_a_mapping(ex):
    # Given only a shiftKnobs mapping
    manifest = {"knobs": [], "shiftKnobs": [{"parameter": 0, "label": "Output"}]}

    # When the script checks its Knob FX mapping
    problems = ex.knob_fx_problems(manifest, num_params=2)

    # Then there are no problems
    assert problems == []


def test_knob_label_of_eight_characters_is_fine_and_nine_is_a_problem(ex):
    # Given one knob labelled with 8 characters and a SHIFT knob with 9
    manifest = {
        "knobs": [{"parameter": 1, "label": "Tilt EQ1"}],
        "shiftKnobs": [{"parameter": 0, "label": "Output Lv"}],
    }

    # When the script checks its Knob FX mapping
    problems = ex.knob_fx_problems(manifest, num_params=2)

    # Then only the 9-character label is a problem
    assert problems == ["shiftKnobs[0]: label 'Output Lv' is longer than 8 characters"]


def test_knob_pointing_past_the_last_parameter_is_a_problem(ex):
    # Given 2 parameters (indices 0 and 1) and a knob on parameter 2
    manifest = {"knobs": [{"parameter": 1, "label": "Tilt"}, {"parameter": 2, "label": "Mix"}]}

    # When the script checks its Knob FX mapping
    problems = ex.knob_fx_problems(manifest, num_params=2)

    # Then that knob is a problem
    assert problems == ["knobs[1]: parameter 2 doesn't exist (the plugin has 2 parameters)"]


def test_knob_without_a_label_is_a_problem(ex):
    # Given a knob with no label (the MPC would show "Param 2", not the parameter's name)
    manifest = {"knobs": [{"parameter": 1}]}

    # When the script checks its Knob FX mapping
    problems = ex.knob_fx_problems(manifest, num_params=2)

    # Then that knob is a problem
    assert problems == ["knobs[0]: has no label"]


# host_sim report


def test_host_sim_report_with_only_pass_and_warn_lines_passes(ex):
    # Given a host_sim run that exits 0 with PASS and WARN lines
    output = (
        "PASS  loads like the MPC\nWARN  clipping on main pass\n"
        "\nResult: PASS with warnings  (9 passed, 1 warnings, 0 failures)\n"
    )

    # When the script reads the result
    ok, detail = ex.host_sim_result(0, output)

    # Then it passes with nothing to report
    assert (ok, detail) == (True, "")


def test_host_sim_report_with_a_fail_line_fails_and_lists_it(ex):
    # Given a host_sim run that exits 1 with one FAIL line among others
    output = (
        "PASS  loads like the MPC\nFAIL  state round-trip: parameter 1 is 0.3, expected 0.7\n"
        "\nResult: FAIL  (9 passed, 0 warnings, 1 failures)\n"
    )

    # When the script reads the result
    ok, detail = ex.host_sim_result(1, output)

    # Then it fails and lists only the FAIL line
    assert (ok, detail) == (False, "FAIL  state round-trip: parameter 1 is 0.3, expected 0.7")


def test_host_sim_crash_fails_and_says_it_crashed(ex):
    # Given a host_sim run that crashed inside the plugin (exit 2, no FAIL lines)
    output = (
        "PASS  loads like the MPC\n"
        "\nCRASH  SIGSEGV\n       phase: render (main pass)\n"
        "       last call into the plugin: processReplacing(128 frames)\n"
    )

    # When the script reads the result
    ok, detail = ex.host_sim_result(2, output)

    # Then it fails, and the detail carries the crash report
    assert ok is False
    assert detail == (
        "CRASH  SIGSEGV\n       phase: render (main pass)\n"
        "       last call into the plugin: processReplacing(128 frames)"
    )


# One copy of the core


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def example_tree(root):
    """A minimal example: one core header, and both wrappers including it by relative path."""
    write(root / "core" / "tilt_eq.h", "#pragma once\n")
    write(root / "juce" / "Source" / "PluginProcessor.h", '#include "../../core/tilt_eq.h"\n')
    write(root / "mpc" / "src" / "TiltEq.cpp", '#include "mpc_plugin.h"\n#include "../../core/tilt_eq.h"\n')
    return root


def test_core_with_both_wrappers_including_it_by_relative_path_has_no_problems(ex, tmp_path):
    # Given one core header, included by relative path from both wrappers
    example = example_tree(tmp_path)

    # When the script checks the core's single copy and the includes
    problems = ex.core_include_problems(example)

    # Then there are no problems
    assert problems == []


def test_wrapper_that_does_not_include_the_core_is_a_problem(ex, tmp_path):
    # Given an MPC wrapper whose sources don't include the core
    example = example_tree(tmp_path)
    write(example / "mpc" / "src" / "TiltEq.cpp", '#include "mpc_plugin.h"\n')

    # When the script checks the core's single copy and the includes
    problems = ex.core_include_problems(example)

    # Then that wrapper is a problem
    assert problems == ["mpc: no source includes the core"]


def test_second_copy_of_a_core_header_is_a_problem(ex, tmp_path):
    # Given a copy of the core header inside the MPC wrapper's src/
    example = example_tree(tmp_path)
    write(example / "mpc" / "src" / "tilt_eq.h", "#pragma once\n")

    # When the script checks the core's single copy and the includes
    problems = ex.core_include_problems(example)

    # Then the copy is a problem
    assert problems == ["mpc/src/tilt_eq.h: second copy of core header tilt_eq.h"]


def test_include_that_resolves_to_a_different_file_is_a_problem(ex, tmp_path):
    # Given a JUCE wrapper that names the core header with one "../" too few,
    # so the include would only work through an include path, not by relative path
    example = example_tree(tmp_path)
    write(example / "juce" / "Source" / "PluginProcessor.h", '#include "../core/tilt_eq.h"\n')

    # When the script checks the core's single copy and the includes
    problems = ex.core_include_problems(example)

    # Then the include is a problem, and so is the wrapper that no longer reaches the core
    assert problems == [
        'juce/Source/PluginProcessor.h: #include "../core/tilt_eq.h" doesn\'t resolve to core/tilt_eq.h',
        "juce: no source includes the core",
    ]


# Builds leave the core untouched


def test_unchanged_core_files_report_no_changes(ex, tmp_path):
    # Given a core folder fingerprinted before the builds
    core = write(tmp_path / "core" / "tilt_eq.h", "#pragma once\n").parent
    before = ex.fingerprint(core)

    # When nothing touches it and it's fingerprinted again
    changes = ex.changed_files(before, ex.fingerprint(core))

    # Then no file has changed
    assert changes == []


def test_edited_or_deleted_core_file_is_reported(ex, tmp_path):
    # Given two core headers fingerprinted before the builds
    core = tmp_path / "core"
    write(core / "tilt_eq.h", "#pragma once\n")
    write(core / "smoother.h", "#pragma once\n")
    before = ex.fingerprint(core)

    # When one is edited, the other deleted, and a new file appears
    write(core / "tilt_eq.h", "#pragma once\n// changed by a build\n")
    (core / "smoother.h").unlink()
    write(core / "generated.h", "#pragma once\n")
    changes = ex.changed_files(before, ex.fingerprint(core))

    # Then all three are reported, in name order
    assert changes == ["generated.h was added", "smoother.h was deleted", "tilt_eq.h was modified"]
