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

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent


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


CHECKS = [
    Check("core behaviour test", run=core_behaviour_test, tools=[CXX]),
]


def main() -> int:
    report = run_checks(CHECKS, find_tool=lambda name: shutil.which(name) is not None)
    for line in report.lines:
        print(line)
    print(f"\n{report.outcome.upper()}")
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
