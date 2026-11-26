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
