#!/usr/bin/env python3
"""End-to-end check for the tilt-EQ example. Runs locally on macOS.

Runs every check in order and keeps going after a failure. A check whose tool is
missing is skipped (with where to get the tool), and so is every check that
depends on a skipped or failed check. Nothing is ever installed.

Outcome and exit code: fail (1) if any check failed or was skipped because a
check it depends on failed; otherwise incomplete (2) if any check was skipped;
otherwise pass (0).

    python3 examples/tilt-eq/check.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

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


CHECKS = [
    Check("core purity", run=core_purity),
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
]


def find_tool(name: str) -> bool:
    if name == "JUCE":
        juce_dir = os.environ.get("JUCE_DIR")
        return bool(juce_dir) and (Path(juce_dir) / "CMakeLists.txt").is_file()
    return shutil.which(name) is not None


def main() -> int:
    report = run_checks(CHECKS, find_tool=find_tool)
    for line in report.lines:
        print(line)
    print(f"\n{report.outcome.upper()}")
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
