#!/usr/bin/env python3
"""Check that audio callbacks are real-time safe.

Finds each real-time body and scans it by matching braces:
- any function named `processBlock` (JUCE)
- any function named `process` whose parameters include `ProcessContext` (the Akai SDK)
- any function with the real-time marker, a `// realtime` comment alone on the
  line before it (use it on the core's entry points)

Inside those bodies it reports allocation (including container growth and local
standard containers), locks,
file or network I/O, and logging or console output as errors, and a
`processBlock` with no denormal protection as a warning. Comments and string
literals are stripped before matching. It doesn't follow calls.

A trailing `// realtime-ok: <reason>` comment suppresses the findings on its
line. The reason is required: a tag without one is itself an error.

    check_realtime.py [--verbose] <file-or-folder>...

Folders are searched for .h, .hpp, .cpp, .cc and .cxx files; a folder with none
is a usage error. Each finding is printed
as `file:line: severity: rule: message`; `--verbose` also lists suppressed
findings as `file:line: suppressed: rule: message (reason: ...)`. Exit codes:
0 no errors (warnings allowed), 1 errors, 2 usage error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SOURCE_SUFFIXES = {".h", ".hpp", ".cpp", ".cc", ".cxx"}

CALLBACK_NAME = re.compile(r"\b(processBlock|process)\s*\(")
FUNCTION_NAME = re.compile(r"\b(\w+)\s*\(")
# What may sit between a parameter list's `)` and the body's `{` in a definition.
QUALIFIERS = re.compile(
    r"\s*(?:(?:const|volatile|override|final|noexcept(?:\s*\([^)]*\))?|&&?)\s*)*"
    r"(?:->\s*[\w:<>,\s*&]+?)?\s*\{"
)
REALTIME_MARKER = re.compile(r"^[ \t]*//[ \t]*realtime[ \t]*$", re.MULTILINE)
OPT_OUT = re.compile(r"//[ \t]*realtime-ok\b[ \t]*:?(.*)$", re.MULTILINE)
RAW_STRING = re.compile(r'(?:u8|[uUL])?R"([^()\\\s]{0,16})\(')
DENORMAL_GUARD = re.compile(
    r"\b(ScopedNoDenormals|disableDenormalisedNumberSupport"
    r"|_MM_SET_FLUSH_ZERO_MODE|_MM_SET_DENORMALS_ZERO_MODE)\b"
)

RULES = [
    ("allocation", re.compile(r"\b(new|delete|malloc|calloc|realloc|free)\b"),
     "heap allocation can block"),
    ("allocation", re.compile(r"\b(push_back|emplace_back|resize|reserve|insert)\s*\("),
     "growing a container can allocate"),
    # A local variable of a standard container type: `std::vector<float> v(n);`,
    # `std::string s;`. A reference or pointer (`&` or `*` after the type) isn't one.
    ("allocation", re.compile(
        r"\bstd\s*::\s*(vector|string|deque|list|map|set|unordered_map|unordered_set)\b"
        r"(?:\s*<[^;{}()]*>)?\s+[A-Za-z_]\w*\s*[;({=]"),
     "a local standard container allocates when it is filled or sized"),
    ("lock", re.compile(
        r"\b((?:recursive_|shared_|timed_|recursive_timed_|shared_timed_)?mutex"
        r"|lock_guard|unique_lock|scoped_lock|shared_lock)\b"),
     "a lock can block on another thread"),
    ("io", re.compile(
        r"\b(fopen|fread|fwrite|fclose|[io]?fstream|File|FileInputStream|FileOutputStream"
        r"|URL|socket|StreamingSocket|DatagramSocket)\b"),
     "file or network I/O can block"),
    ("logging", re.compile(r"\b(cout|cerr|printf|fprintf|DBG|Logger|mpc\s*::\s*log)\b"),
     "logging or console output can block"),
]


def blank(text: str) -> str:
    """Replace every character but newlines with a space, so line numbers survive."""
    return re.sub(r"[^\n]", " ", text)


def find_end(text: str, token: str, start: int) -> int:
    """Offset just past the next `token` at or after `start`, or the end of `text`."""
    found = text.find(token, start)
    return len(text) if found < 0 else found + len(token)


def literal_end(text: str, start: int) -> int:
    """End offset of the string or char literal whose opening quote is at `start`."""
    quote = text[start]
    i = start + 1
    while i < len(text) and text[i] not in (quote, "\n"):
        i += 2 if text[i] == "\\" else 1
    return min(i + 1, len(text))


def strip(text: str) -> str:
    """`text` with comments and string or char literals blanked, newlines kept."""
    out: list[str] = []
    i = 0
    while i < len(text):
        raw = RAW_STRING.match(text, i)
        after_identifier = i > 0 and (text[i - 1].isalnum() or text[i - 1] == "_")
        if text.startswith("//", i):
            newline = text.find("\n", i)
            end, code = (len(text) if newline < 0 else newline), False
        elif text.startswith("/*", i):
            end, code = find_end(text, "*/", i + 2), False
        elif raw and not after_identifier:
            end, code = find_end(text, f"){raw.group(1)}\"", raw.end()), False
        elif text[i] in "\"'":
            end, code = literal_end(text, i), False
        else:
            end, code = i + 1, True
        out.append(text[i:end] if code else blank(text[i:end]))
        i = end
    return "".join(out)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


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


def body_after(code: str, name: re.Match) -> tuple[int, int] | None:
    """Braces of the body when `name(` starts a definition, else None (a declaration or call)."""
    params_open = name.end() - 1
    params_close = matching(code, params_open, "(", ")")
    definition = QUALIFIERS.match(code, params_close + 1)
    if not definition:
        return None
    body_open = definition.end() - 1
    return body_open, matching(code, body_open, "{", "}")


def realtime_bodies(text: str, code: str) -> dict[tuple[int, int], tuple[str, int]]:
    """Each real-time body's (start, end) braces, mapped to (function name, name offset)."""
    bodies = {}
    for name in CALLBACK_NAME.finditer(code):
        params = code[name.end():matching(code, name.end() - 1, "(", ")")]
        if name.group(1) == "process" and "ProcessContext" not in params:
            continue
        body = body_after(code, name)
        if body:
            bodies[body] = (name.group(1), name.start())
    for marker in REALTIME_MARKER.finditer(text):
        name = FUNCTION_NAME.search(code, marker.end())
        if name and not re.search(r"[;{}]", code[marker.end():name.start()]):
            body = body_after(code, name)
            if body:
                bodies.setdefault(body, (name.group(1), name.start()))
    return bodies


def findings(code: str, bodies: dict) -> list[tuple[int, str, str, str]]:
    """(line, severity, rule, message) for every rule break inside the bodies."""
    found = []
    for (start, end), (name, name_at) in bodies.items():
        for rule, pattern, why in RULES:
            for hit in pattern.finditer(code, start, end):
                message = f"`{hit.group(1)}` in a real-time body: {why}"
                found.append((line_of(code, hit.start()), "error", rule, message))
        if name == "processBlock" and not DENORMAL_GUARD.search(code, start, end):
            message = "no denormal protection: add `juce::ScopedNoDenormals` at the top"
            found.append((line_of(code, name_at), "warning", "denormal", message))
    return found


def opt_outs(text: str, code: str) -> dict[int, str]:
    """Line -> reason (possibly empty) for each opt-out tag that sits in a comment."""
    tags = {}
    for tag in OPT_OUT.finditer(text):
        if code[tag.start()] == " ":  # blanked, so the `//` starts a real comment
            tags[line_of(text, tag.start())] = tag.group(1).strip()
    return tags


def check(path: Path, verbose: bool) -> int:
    text = path.read_text()
    code = strip(text)
    bodies = realtime_bodies(text, code)
    if not bodies:
        print(f"{path}: no real-time body found")
    tags = opt_outs(text, code)
    report = [(line, "error", "opt-out", "opt-out marker needs a reason: "
               "`// realtime-ok: <why this line is safe>`")
              for line, reason in tags.items() if not reason]
    for line, severity, rule, message in findings(code, bodies):
        reason = tags.get(line)
        if reason:
            if verbose:
                print(f"{path}:{line}: suppressed: {rule}: {message} (reason: {reason})")
        else:
            report.append((line, severity, rule, message))
    for line, severity, rule, message in sorted(report):
        print(f"{path}:{line}: {severity}: {rule}: {message}")
    return 1 if any(severity == "error" for _, severity, _, _ in report) else 0


def source_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.suffix in SOURCE_SUFFIXES and p.is_file())
    return [path]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check that audio callbacks are real-time safe.")
    parser.add_argument("paths", nargs="+", type=Path, help="source files or folders")
    parser.add_argument("--verbose", action="store_true",
                        help="also list suppressed findings with their reasons")
    args = parser.parse_args(argv)
    for path in args.paths:
        if not path.exists():
            parser.error(f"no such file or folder: {path}")
    files = [f for p in args.paths for f in source_files(p)]
    if not files:
        parser.error("no source files (.h, .hpp, .cpp, .cc, .cxx) found")

    status = 0
    for path in files:
        status = max(status, check(path, args.verbose))
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
