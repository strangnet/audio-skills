#!/usr/bin/env python3
"""End-to-end check for the tilt-EQ example. Runs locally on macOS.

Runs every check in order and keeps going after a failure. A check whose tool is
missing is skipped (with where to get the tool), and so is every check that
depends on a skipped or failed check. Nothing is ever installed.

Outcome and exit code: fail (1) if any check failed or was skipped because a
check it depends on failed; otherwise incomplete (2) if any check was skipped;
otherwise pass (0).

    JUCE_DIR=<JUCE 9.0.6> MPC_SDK=<Akai SDK clone> python3 examples/tilt-eq/check.py

zig comes from $ZIG or PATH and is handed to the SDK's build tool, so that tool
never installs zig itself. The SDK's build tool writes into examples/tilt-eq/mpc/build/
(gitignored) and, on first use, builds host_sim into the SDK clone's .sdk-tools/.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BUILD = REPO / "build" / "tilt-eq"
PURITY_CHECKER = REPO / "skills" / "audio-portable-core" / "scripts" / "check_core_purity.py"
REALTIME_CHECKER = REPO / "skills" / "audio-dsp" / "scripts" / "check_realtime.py"


@dataclass
class Tool:
    name: str
    hint: str


@dataclass
class Check:
    name: str
    run: Callable[[], tuple[bool, str]]
    tools: list[Tool] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Report:
    outcome: str
    exit_code: int
    lines: list[str] = field(default_factory=list)


def skip_reason(
    check: Check, failed_checks: set[str], skipped_checks: set[str], find_tool: Callable[[str], bool]
) -> tuple[str, str] | None:
    """Why `check` can't run, and whether that counts as "fail" or "incomplete"."""
    for dependency in check.depends_on:
        if dependency in failed_checks:
            return f"depends on failed check {dependency}", "fail"
    for dependency in check.depends_on:
        if dependency in skipped_checks:
            return f"depends on skipped check {dependency}", "incomplete"
    for tool in check.tools:
        if not find_tool(tool.name):
            return f"{tool.name} not found (get it from {tool.hint})", "incomplete"
    return None


def run_checks(checks: list[Check], find_tool: Callable[[str], bool]) -> Report:
    lines = []
    failed_checks: set[str] = set()
    skipped_checks: set[str] = set()
    for check in checks:
        skip = skip_reason(check, failed_checks, skipped_checks, find_tool)
        if skip:
            reason, counts_as = skip
            lines.append(f"SKIP  {check.name}: {reason}")
            (failed_checks if counts_as == "fail" else skipped_checks).add(check.name)
            continue
        try:
            ok, detail = check.run()
        except Exception as error:
            ok, detail = False, f"crashed: {type(error).__name__}: {error}"
        if ok:
            lines.append(f"PASS  {check.name}")
        else:
            lines.append(f"FAIL  {check.name}: {detail}")
            failed_checks.add(check.name)
    if failed_checks:
        return Report(outcome="fail", exit_code=1, lines=lines)
    if skipped_checks:
        return Report(outcome="incomplete", exit_code=2, lines=lines)
    return Report(outcome="pass", exit_code=0, lines=lines)


# --- Real checks -------------------------------------------------------------

CXX = Tool("c++", hint="the Xcode Command Line Tools: xcode-select --install")


def core_purity() -> tuple[bool, str]:
    run = subprocess.run(
        [sys.executable, str(PURITY_CHECKER), str(HERE / "core")], capture_output=True, text=True
    )
    return run.returncode == 0, (run.stdout + run.stderr).strip()


def realtime_safety() -> tuple[bool, str]:
    """The core and every wrapper folder that exists pass the real-time checker."""
    folders = [HERE / name for name in ("core", "juce", "mpc") if (HERE / name).is_dir()]
    run = subprocess.run(
        [sys.executable, str(REALTIME_CHECKER), *map(str, folders)],
        capture_output=True, text=True,
    )
    return run.returncode == 0, (run.stdout + run.stderr).strip()


def core_behaviour_test() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        binary = Path(tmp) / "core_test"
        build = subprocess.run(
            ["c++", "-std=c++17", "-O2", "-Wall", "-o", str(binary),
             str(HERE / "tests" / "core_test.cpp")],
            capture_output=True, text=True,
        )
        if build.returncode != 0:
            return False, "build failed:\n" + build.stderr
        run = subprocess.run([str(binary)], capture_output=True, text=True)
        return run.returncode == 0, run.stdout.strip()


CMAKE = Tool("cmake", hint="Homebrew: brew install cmake")
NINJA = Tool("ninja", hint="Homebrew: brew install ninja")
JUCE = Tool("JUCE", hint="a JUCE 9.0.6 checkout, with JUCE_DIR set to its path")
PLUGINVAL = Tool("pluginval", hint="https://github.com/Tracktion/pluginval/releases")
CLAP_VALIDATOR = Tool("clap-validator", hint="https://github.com/free-audio/clap-validator/releases")
AUVAL = Tool("auval", hint="macOS (it ships with the system)")

JUCE_BUILD = BUILD / "juce"
ARTEFACTS = JUCE_BUILD / "TiltEq_artefacts" / "Release"
PRODUCT = "Tilt EQ"
# The AU's type, subtype and manufacturer codes, as set in the JUCE wrapper's CMakeLists.txt.
AU_CODES = ["aufx", "Tilt", "Stng"]


def run_tool(command: list[str]) -> tuple[bool, str]:
    run = subprocess.run(command, capture_output=True, text=True)
    output = (run.stdout + run.stderr).strip()
    return run.returncode == 0, output if run.returncode != 0 else ""


def juce_build() -> tuple[bool, str]:
    ok, output = run_tool([
        "cmake", "-S", str(HERE / "juce"), "-B", str(JUCE_BUILD), "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release", f"-DJUCE_DIR={os.environ['JUCE_DIR']}",
    ])
    if not ok:
        return False, "configure failed:\n" + output[-3000:]
    ok, output = run_tool(["cmake", "--build", str(JUCE_BUILD), "--config", "Release"])
    return ok, "" if ok else "build failed:\n" + output[-3000:]


COMPONENTS = Path.home() / "Library" / "Audio" / "Plug-Ins" / "Components"
INSTALLED_AU = COMPONENTS / f"{PRODUCT}.component"


def pluginval(plugin: Path) -> Callable[[], tuple[bool, str]]:
    def check() -> tuple[bool, str]:
        ok, output = run_tool(
            ["pluginval", "--strictness-level", "10", "--validate-in-process", "--validate", str(plugin)]
        )
        return ok, output[-3000:]
    return check


def clap_validator() -> tuple[bool, str]:
    ok, output = run_tool(["clap-validator", "validate", str(ARTEFACTS / "CLAP" / f"{PRODUCT}.clap")])
    return ok, output[-3000:]


def install_au() -> tuple[bool, str]:
    """Copy the AU into the user's Components folder so macOS registers it.

    AU validators only see registered components. This is the one place the
    script writes outside the repo; it replaces only this plugin's component.
    """
    COMPONENTS.mkdir(parents=True, exist_ok=True)
    if INSTALLED_AU.exists():
        shutil.rmtree(INSTALLED_AU)
    shutil.copytree(ARTEFACTS / "AU" / f"{PRODUCT}.component", INSTALLED_AU)
    # Make the AU registrar rescan; it restarts on demand.
    subprocess.run(["killall", "-9", "AudioComponentRegistrar"], capture_output=True)
    return True, ""


def auval() -> tuple[bool, str]:
    ok, output = run_tool(["auval", "-v", *AU_CODES])
    return ok, output[-3000:]


# --- MPC wrapper ---------------------------------------------------------------


def find_zig(environ: Mapping[str, str], which: Callable[[str], str | None]) -> Path | None:
    """The zig to hand the SDK's build tool, so the tool never installs one itself.

    $ZIG wins when set; if it names a missing file, there is no zig rather than a
    silent fallback to a different one.
    """
    if environ.get("ZIG"):
        chosen = Path(environ["ZIG"])
        return chosen if chosen.is_file() else None
    on_path = which("zig")
    return Path(on_path) if on_path else None


def find_mpc_sdk(environ: Mapping[str, str]) -> Path | None:
    """The Akai SDK checkout named by $MPC_SDK, if it holds the SDK's build tool."""
    if not environ.get("MPC_SDK"):
        return None
    sdk = Path(environ["MPC_SDK"])
    return sdk if (sdk / "tools" / "build.py").is_file() else None


def mpc_build_command(sdk: Path, project: Path, zig: Path, python: str) -> list[str]:
    """The SDK's build tool, called with absolute paths and the zig this script found.

    Builds native (for host_sim), arm32 and arm64, and runs the SDK's validation.
    """
    return [
        python, str((sdk / "tools" / "build.py").absolute()), str(project.absolute()),
        "--target", "all", "--toolchain", "zig", "--zig", str(zig.absolute()),
    ]


MAX_KNOB_LABEL = 8  # three knob labels share the MPC's 320-pixel screen (SDK docs/knob-fx.md)


def knob_fx_problems(manifest: dict, num_params: int) -> list[str]:
    """What's wrong with the manifest's Knob FX mapping, if anything.

    Every MPC effect needs one; without it the knobs drive parameters 0-5 as "Param 1" to "Param 6".
    """
    if not (manifest.get("knobs") or manifest.get("shiftKnobs")):
        return ["plugin.json has no Knob FX mapping (knobs or shiftKnobs)"]
    problems = []
    for key in ("knobs", "shiftKnobs"):
        for i, knob in enumerate(manifest.get(key, [])):
            where = f"{key}[{i}]"
            parameter = knob["parameter"]
            if not 0 <= parameter < num_params:
                problems.append(
                    f"{where}: parameter {parameter} doesn't exist (the plugin has {num_params} parameters)"
                )
            label = knob.get("label")
            if not label:
                problems.append(f"{where}: has no label")
            elif len(label) > MAX_KNOB_LABEL:
                problems.append(f"{where}: label '{label}' is longer than {MAX_KNOB_LABEL} characters")
    return problems


HOST_SIM_CRASHED = 2  # host_sim's exit code when the plugin crashed (SDK tools/host-sim/README.md)


def host_sim_result(returncode: int, output: str) -> tuple[bool, str]:
    """Pass when host_sim reports no FAIL; WARN lines are allowed. On failure, the
    detail is the FAIL lines, or the crash report when the plugin crashed."""
    if returncode == HOST_SIM_CRASHED:
        crash = output[output.find("CRASH"):] if "CRASH" in output else output
        return False, crash.strip()
    fails = [line for line in output.splitlines() if line.startswith("FAIL ")]
    return returncode == 0 and not fails, "\n".join(fails)


WRAPPERS = ("juce", "mpc")
SOURCE_SUFFIXES = (".h", ".hpp", ".cpp", ".cc", ".cxx")
QUOTED_INCLUDE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.MULTILINE)


def quoted_includes(example: Path, wrapper: str):
    """Each (source file, included name) for the wrapper's `#include "..."` lines."""
    for source in sorted((example / wrapper).rglob("*")):
        if source.suffix in SOURCE_SUFFIXES and source.is_file():
            for name in QUOTED_INCLUDE.findall(source.read_text()):
                yield source, name


def core_include_problems(example: Path) -> list[str]:
    """Exactly one copy of each core header exists, and both wrappers include it by
    a relative path that resolves to that copy (not through an include path)."""
    core_headers = {path.resolve(): path for path in (example / "core").glob("*.h")}
    core_names = {path.name: path for path in core_headers.values()}

    def shown(path: Path) -> str:
        return path.relative_to(example).as_posix()

    problems = [
        f"{shown(path)}: second copy of core header {path.name}"
        for path in sorted(example.rglob("*"))
        if path.name in core_names and path.resolve() not in core_headers
    ]
    for wrapper in WRAPPERS:
        included = False
        for source, name in quoted_includes(example, wrapper):
            if (source.parent / name).resolve() in core_headers:
                included = True
            elif Path(name).name in core_names:
                problems.append(
                    f'{shown(source)}: #include "{name}" doesn\'t resolve to '
                    f"{shown(core_names[Path(name).name])}"
                )
        if not included:
            problems.append(f"{wrapper}: no source includes the core")
    return problems


def fingerprint(folder: Path) -> dict[str, str]:
    """A SHA-256 per file in the folder, keyed by its path relative to the folder."""
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in folder.rglob("*")
        if path.is_file()
    }


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Each file that was modified, deleted or added between two fingerprints."""
    changes = []
    for name in sorted(before.keys() | after.keys()):
        if name not in after:
            changes.append(f"{name} was deleted")
        elif name not in before:
            changes.append(f"{name} was added")
        elif before[name] != after[name]:
            changes.append(f"{name} was modified")
    return changes


ZIG = Tool("zig", hint="Homebrew: brew install zig, or set ZIG to a zig executable")
MPC_SDK = Tool("MPC SDK", hint="a clone of Akai's MPC Plugin Builder SDK, with MPC_SDK set to its path")

MPC_PROJECT = HERE / "mpc"
MPC_BUILD = MPC_PROJECT / "build"  # where the SDK's build tool writes; gitignored
MPC_NATIVE = MPC_BUILD / "native" / "tilt-eq.dylib"


def one_core_copy() -> tuple[bool, str]:
    problems = core_include_problems(HERE)
    return not problems, "\n".join(problems)


def mpc_build() -> tuple[bool, str]:
    """Native, arm32 and arm64 builds plus the SDK's validation, through the SDK's build tool."""
    sdk, zig = find_mpc_sdk(os.environ), find_zig(os.environ, shutil.which)
    assert sdk is not None and zig is not None  # run_checks skips this check otherwise
    ok, output = run_tool(mpc_build_command(sdk, MPC_PROJECT, zig, python=sys.executable))
    return ok, output[-3000:]


def mpc_knob_fx() -> tuple[bool, str]:
    manifest = json.loads((MPC_PROJECT / "plugin.json").read_text())
    params = json.loads((MPC_BUILD / "params.json").read_text())["params"]
    problems = knob_fx_problems(manifest, num_params=len(params))
    return not problems, "\n".join(problems)


def mpc_host_sim() -> tuple[bool, str]:
    sdk = find_mpc_sdk(os.environ)
    assert sdk is not None  # run_checks skips this check otherwise
    run = subprocess.run(
        [str(sdk / ".sdk-tools" / "host_sim"), str(MPC_NATIVE), "test"], capture_output=True, text=True
    )
    return host_sim_result(run.returncode, run.stdout + run.stderr)


# Taken when the script loads, before any build runs.
CORE_BEFORE_BUILDS = fingerprint(HERE / "core")


def core_unchanged() -> tuple[bool, str]:
    changes = changed_files(CORE_BEFORE_BUILDS, fingerprint(HERE / "core"))
    return not changes, "\n".join(changes)


CHECKS = [
    Check("core purity", run=core_purity),
    Check("one copy of the core, included by both wrappers", run=one_core_copy),
    Check("real-time safety", run=realtime_safety),
    Check("core behaviour test", run=core_behaviour_test, tools=[CXX]),
    Check("JUCE build (VST3, AU, CLAP)", run=juce_build, tools=[CMAKE, NINJA, JUCE]),
    Check("pluginval VST3", run=pluginval(ARTEFACTS / "VST3" / f"{PRODUCT}.vst3"),
          tools=[PLUGINVAL], depends_on=["JUCE build (VST3, AU, CLAP)"]),
    Check("clap-validator", run=clap_validator, tools=[CLAP_VALIDATOR],
          depends_on=["JUCE build (VST3, AU, CLAP)"]),
    Check("install AU for validation", run=install_au, depends_on=["JUCE build (VST3, AU, CLAP)"]),
    Check("pluginval AU", run=pluginval(INSTALLED_AU), tools=[PLUGINVAL],
          depends_on=["install AU for validation"]),
    Check("auval", run=auval, tools=[AUVAL], depends_on=["install AU for validation"]),
    Check("MPC build (arm32, arm64, SDK validation)", run=mpc_build, tools=[MPC_SDK, ZIG]),
    Check("MPC Knob FX mapping", run=mpc_knob_fx,
          depends_on=["MPC build (arm32, arm64, SDK validation)"]),
    Check("host_sim", run=mpc_host_sim, depends_on=["MPC build (arm32, arm64, SDK validation)"]),
    Check("builds left the core unchanged", run=core_unchanged),
]


def find_tool(name: str) -> bool:
    if name == "JUCE":
        juce_dir = os.environ.get("JUCE_DIR")
        return bool(juce_dir) and (Path(juce_dir) / "CMakeLists.txt").is_file()
    if name == "zig":
        return find_zig(os.environ, shutil.which) is not None
    if name == "MPC SDK":
        return find_mpc_sdk(os.environ) is not None
    return shutil.which(name) is not None


def main() -> int:
    report = run_checks(CHECKS, find_tool=find_tool)
    for line in report.lines:
        print(line)
    print(f"\n{report.outcome.upper()}")
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
