"""Core-purity check: a core folder must be header-only C++17 that includes only
standard-library headers and its own headers, and never names JUCE or the MPC SDK."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "audio-portable-core" / "scripts" / "check_core_purity.py"
EXAMPLE_CHECK = REPO / "examples" / "tilt-eq" / "check.py"


def load_example_check():
    spec = importlib.util.spec_from_file_location("example_check", EXAMPLE_CHECK)
    assert spec is not None and spec.loader is not None, f"cannot load {EXAMPLE_CHECK}"
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve postponed annotations through sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write(path, text=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run_check(*paths):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)], capture_output=True, text=True
    )


# Zero


def test_clean_core_has_no_findings_and_passes(tmp_path):
    # Given a core whose headers include only standard headers and each other
    core = tmp_path / "core"
    write(core / "params.h", "#pragma once\n#include <cstdint>\n#include <array>\n")
    write(
        core / "tilt.h",
        '#pragma once\n#include <cmath>\n#include "params.h"\n'
        "inline float gain(float db) { return std::pow(10.0f, db / 20.0f); }\n",
    )

    # When the core-purity check runs on the core folder
    result = run_check(core)

    # Then it reports nothing and exits with success
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


# One


def test_juce_include_name_and_macro_are_each_reported_even_without_an_include(tmp_path):
    # Given one core header that includes a JUCE header
    core = tmp_path / "core"
    write(core / "a.h", "#pragma once\n#include <juce_core/juce_core.h>\n")
    # And another that uses a juce:: name and a JUCE_ macro with no JUCE include
    write(
        core / "b.h",
        "#pragma once\n#include <cmath>\n"
        "inline float f(float x) { return juce::jlimit(0.0f, 1.0f, x); }\n"
        "JUCE_DECLARE_NON_COPYABLE(Thing)\n",
    )

    # When the core-purity check runs
    result = run_check(core)

    # Then each one is reported as an error with file:line, and the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    assert len(lines) == 3, result.stdout
    assert lines[0].startswith(f"{core / 'a.h'}:2: error: ")
    assert lines[1].startswith(f"{core / 'b.h'}:3: error: ")
    assert lines[2].startswith(f"{core / 'b.h'}:4: error: ")


def test_sdk_include_and_mpc_name_are_reported(tmp_path):
    # Given a core header that includes an SDK header and uses an mpc:: name
    core = tmp_path / "core"
    write(
        core / "tilt.h",
        '#pragma once\n#include "mpc/Plugin.h"\n'
        "inline void f(mpc::ProcessContext& c) {}\n",
    )

    # When the core-purity check runs
    result = run_check(core)

    # Then both are reported as errors with file:line, and the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    assert len(lines) == 2, result.stdout
    assert lines[0].startswith(f"{core / 'tilt.h'}:2: error: ")
    assert lines[1].startswith(f"{core / 'tilt.h'}:3: error: ")


def test_non_standard_third_party_include_is_reported(tmp_path):
    # Given a core header that includes many C++17 standard headers and one third-party header
    core = tmp_path / "core"
    standard = [
        "algorithm", "atomic", "cassert", "cfloat", "climits", "cstddef", "cstdio",
        "cstdlib", "cstring", "functional", "limits", "memory", "numeric", "optional",
        "string", "string_view", "type_traits", "utility", "variant", "vector",
    ]
    write(
        core / "tilt.h",
        "#pragma once\n"
        + "".join(f"#include <{name}>\n" for name in standard)
        + "#include <Eigen/Dense>\n",
    )

    # When the core-purity check runs
    result = run_check(core)

    # Then only the third-party include is reported, and the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{core / 'tilt.h'}:{len(standard) + 2}: error: include: "
        "<Eigen/Dense> is not a C++17 standard header"
    ]


def test_cpp_file_in_core_is_reported_as_not_header_only(tmp_path):
    # Given a core folder with a clean header and a .cpp file
    core = tmp_path / "core"
    write(core / "tilt.h", "#pragma once\nfloat gain(float db);\n")
    write(core / "tilt.cpp", '#include "tilt.h"\nfloat gain(float db) { return db; }\n')

    # When the core-purity check runs
    result = run_check(core)

    # Then the .cpp file is reported as breaking header-only, and the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    assert len(lines) == 1, result.stdout
    assert lines[0].startswith(f"{core / 'tilt.cpp'}:1: error: header-only: ")


# Boundaries


def test_juce_name_only_in_comment_or_string_literal_is_not_reported(tmp_path):
    # Given a core header that mentions juce::, mpc:: and JUCE_ only in comments and strings
    core = tmp_path / "core"
    write(
        core / "tilt.h",
        "#pragma once\n"
        "// Unlike juce::dsp::IIR, this filter is portable.\n"
        "/* Replaces juce::SmoothedValue\n   and JUCE_LEAK_DETECTOR. */\n"
        "#include <string> // not <juce_core/juce_core.h>\n"
        'inline const char* name() { return "juce::Tilt // \\" mpc::Tilt"; }\n'
        "inline char sep() { return '\"'; } // a quote char must not open a string\n"
        'inline const char* raw() { return R"x(juce::Raw ")" JUCE_X)x"; }\n',
    )

    # When the core-purity check runs
    result = run_check(core)

    # Then nothing is reported and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


# Interface


def test_example_core_passes_the_core_purity_check():
    # Given the tilt-EQ example check script and its "core purity" check
    checks = {check.name: check for check in load_example_check().CHECKS}
    core_purity = checks["core purity"]

    # When the check runs on the example core
    ok, detail = core_purity.run()

    # Then it passes and needs no tools beyond Python
    assert ok, detail
    assert core_purity.tools == []


def test_a_header_file_path_is_checked_against_its_own_folder(tmp_path):
    # Given a core header that includes a sibling header and uses a juce:: name
    core = tmp_path / "core"
    write(core / "params.h", "#pragma once\n")
    write(core / "tilt.h", '#pragma once\n#include "params.h"\njuce::String s;\n')

    # When the core-purity check runs on that header file alone
    result = run_check(core / "tilt.h")

    # Then the sibling include is allowed and only the juce:: name is reported
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{core / 'tilt.h'}:3: error: juce-name: JUCE name in the core: juce::"
    ]


# Exceptions


@pytest.mark.parametrize(
    "make_paths",
    [
        lambda tmp: [],
        lambda tmp: [tmp / "does-not-exist"],
        lambda tmp: [tmp],
        lambda tmp: [write(tmp / "core" / "tilt.h", "#pragma once\n") or tmp / "core", tmp / "gone"],
        lambda tmp: [write(tmp / "notes.txt", "juce::\n") or tmp],
    ],
    ids=["no path", "missing path", "empty folder", "one of two paths missing", "no headers"],
)
def test_missing_path_or_no_headers_prints_usage_and_exits_with_usage_error(tmp_path, make_paths):
    # Given a missing path, or a path with no headers
    paths = make_paths(tmp_path)

    # When the core-purity check runs on it
    result = run_check(*paths)

    # Then it prints usage and exits with the usage-error code, distinct from failure
    assert result.returncode == 2, result.stdout + result.stderr
    assert "usage:" in result.stderr
    assert result.stdout == ""
