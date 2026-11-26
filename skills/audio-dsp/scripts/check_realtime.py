#!/usr/bin/env python3
"""Check that audio callbacks are real-time safe.

Finds each real-time body by its signature and scans it by matching braces:
any function named `processBlock` (JUCE), and any function named `process`
whose parameters include `ProcessContext` (the Akai SDK). Inside those bodies
it reports allocation (including container growth), locks, file or network
I/O, and logging or console output. It doesn't follow calls.

    check_realtime.py <file-or-folder>...

Folders are searched for .h, .hpp, .cpp and .cc files. Each finding is printed
as `file:line: severity: rule: message`. Exit codes: 0 no errors, 1 errors,
2 usage error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SOURCE_SUFFIXES = {".h", ".hpp", ".cpp", ".cc"}

CALLBACK_NAME = re.compile(r"\b(processBlock|process)\s*\(")
# What may sit between a parameter list's `)` and the body's `{` in a definition.
QUALIFIERS = re.compile(
    r"\s*(?:(?:const|volatile|override|final|noexcept(?:\s*\([^)]*\))?|&&?)\s*)*"
    r"(?:->\s*[\w:<>,\s*&]+?)?\s*\{"
)

RULES = [
    ("allocation", re.compile(r"\b(new|delete|malloc|calloc|realloc|free)\b"),
     "heap allocation can block"),
    ("allocation", re.compile(r"\b(push_back|emplace_back|resize|reserve|insert)\s*\("),
     "growing a container can allocate"),
    ("lock", re.compile(
        r"\b((?:recursive_|shared_|timed_|recursive_timed_|shared_timed_)?mutex"
        r"|lock_guard|unique_lock|scoped_lock|shared_lock)\b"),
     "a lock can block on another thread"),
    ("io", re.compile(
        r"\b(fopen|fread|fwrite|fclose|[io]?fstream|File|FileInputStream|FileOutputStream"
        r"|URL|socket|StreamingSocket|DatagramSocket)\b"),
     "file or network I/O can block"),
    ("logging", re.compile(r"\b(cout|cerr|printf|fprintf|DBG|Logger)\b"),
     "logging or console output can block"),
]


def matching(text: str, start: int, open_ch: str, close_ch: str) -> int:
    """Index of the bracket that closes the one at `start`, or len(text) if none."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return i
    return len(text)


def realtime_bodies(text: str) -> list[tuple[int, int]]:
    """(start, end) offsets of each real-time function body's braces."""
    bodies = []
    for match in CALLBACK_NAME.finditer(text):
        params_open = match.end() - 1
        params_close = matching(text, params_open, "(", ")")
        if match.group(1) == "process" and "ProcessContext" not in text[params_open:params_close]:
            continue
        definition = QUALIFIERS.match(text, params_close + 1)
        if definition:  # otherwise a declaration or a call
            body_open = definition.end() - 1
            bodies.append((body_open, matching(text, body_open, "{", "}")))
    return bodies


def findings(text: str, bodies: list[tuple[int, int]]) -> list[tuple[int, str, str]]:
    """(line, rule, message) for every rule break inside the bodies."""
    found = []
    for start, end in bodies:
        for rule, pattern, why in RULES:
            for hit in pattern.finditer(text, start, end):
                line = text.count("\n", 0, hit.start()) + 1
                found.append((line, rule, f"`{hit.group(1)}` in a real-time body: {why}"))
    return sorted(found)


def source_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.suffix in SOURCE_SUFFIXES and p.is_file())
    return [path]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check that audio callbacks are real-time safe.")
    parser.add_argument("paths", nargs="+", type=Path, help="source files or folders")
    args = parser.parse_args(argv)
    for path in args.paths:
        if not path.exists():
            parser.error(f"no such file or folder: {path}")

    status = 0
    for path in [f for p in args.paths for f in source_files(p)]:
        text = path.read_text()
        bodies = realtime_bodies(text)
        if not bodies:
            print(f"{path}: no real-time body found")
        for line, rule, message in findings(text, bodies):
            print(f"{path}:{line}: error: {rule}: {message}")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
