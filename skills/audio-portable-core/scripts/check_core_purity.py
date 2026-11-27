#!/usr/bin/env python3
"""Check that a portable DSP core is pure: header-only C++17 using only the standard library.

Comments and string literals are stripped before matching. Headers are .h and .hpp;
sources are .cpp, .cc and .cxx. Allowed includes are the C++17 standard library
headers (with the C compatibility headers in their <cname> form) and quoted includes
that resolve to a file inside the core folder. A deprecated C header such as
<math.h> is a warning naming its replacement. Reported as errors: any other include,
any juce:: or mpc:: name, any JUCE_ macro (whatever the includes), and any source
file in the core, even when the core has no headers.

    check_core_purity.py <core folder>...

Prints `file:line: severity: rule: message` per finding. Exit 0 = no errors
(warnings allowed), 1 = errors, 2 = usage error (no path, a missing path, or no
headers or source files found).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterator
from pathlib import Path

# C++17 standard library headers ([headers] in ISO/IEC 14882:2017), including the
# C compatibility headers in their <cname> form.
STANDARD_HEADERS = frozenset(
    """
    algorithm any array atomic bitset chrono charconv codecvt complex
    condition_variable deque exception execution filesystem forward_list fstream
    functional future initializer_list iomanip ios iosfwd iostream istream
    iterator limits list locale map memory memory_resource mutex new numeric
    optional ostream queue random ratio regex scoped_allocator set shared_mutex
    sstream stack stdexcept streambuf string string_view strstream system_error
    thread tuple type_traits typeindex typeinfo unordered_map unordered_set
    utility valarray variant vector
    cassert ccomplex cctype cerrno cfenv cfloat cinttypes ciso646 climits
    clocale cmath csetjmp csignal cstdalign cstdarg cstdbool cstddef cstdint
    cstdio cstdlib cstring ctgmath ctime cuchar cwchar cwctype
    """.split()
)

INCLUDE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]*)[>"]', re.MULTILINE)
NAMES = (
    (re.compile(r"\bjuce\s*::"), "juce-name", "JUCE name"),
    (re.compile(r"\bJUCE_\w*"), "juce-macro", "JUCE macro"),
    (re.compile(r"\bmpc\s*::"), "mpc-name", "MPC SDK name"),
)


RAW_STRING = re.compile(r'(?:u8|[uUL])?R"([^()\\\s]{0,16})\(')


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


def strip(text: str) -> tuple[str, str]:
    """Return (text without comments, text without comments or string literals).

    Both keep every newline, so offsets map to the same line numbers as `text`.
    """
    no_comments: list[str] = []
    bare: list[str] = []
    i = 0
    while i < len(text):
        raw = RAW_STRING.match(text, i)
        after_identifier = i > 0 and (text[i - 1].isalnum() or text[i - 1] == "_")
        if text.startswith("//", i):
            newline = text.find("\n", i)
            end, kind = (len(text) if newline < 0 else newline), "comment"
        elif text.startswith("/*", i):
            end, kind = find_end(text, "*/", i + 2), "comment"
        elif raw and not after_identifier:
            end, kind = find_end(text, f"){raw.group(1)}\"", raw.end()), "literal"
        elif text[i] in "\"'":
            end, kind = literal_end(text, i), "literal"
        else:
            end, kind = i + 1, "code"
        chunk = text[i:end]
        no_comments.append(blank(chunk) if kind == "comment" else chunk)
        bare.append(chunk if kind == "code" else blank(chunk))
        i = end
    return "".join(no_comments), "".join(bare)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


# Deprecated C headers in C++17 ([depr.c.headers]) and what to write instead. The
# <cname> forms of complex.h, tgmath.h, stdbool.h, stdalign.h and iso646.h are
# themselves deprecated or empty in C++, so those name the real replacement.
DEPRECATED_C_HEADERS = {
    **{f"{name}.h": f"use <c{name}>" for name in (
        "assert", "ctype", "errno", "fenv", "float", "inttypes", "limits", "locale", "math",
        "setjmp", "signal", "stdarg", "stddef", "stdint", "stdio", "stdlib", "string", "time",
        "uchar", "wchar", "wctype")},
    "complex.h": "use <complex>",
    "tgmath.h": "use <cmath> and <complex>",
    "stdbool.h": "remove it: bool, true and false are built into C++",
    "stdalign.h": "remove it: alignas and alignof are built into C++",
    "iso646.h": "remove it: and, or and not are built into C++",
}


def include_problem(kind: str, name: str, header: Path, core: Path) -> tuple[str, str, str] | None:
    """(severity, rule, message) for an include the core must not have, or None."""
    if kind == "<":
        if name in STANDARD_HEADERS:
            return None
        if name in DEPRECATED_C_HEADERS:
            return ("warning", "deprecated-header",
                    f"<{name}> is deprecated in C++; {DEPRECATED_C_HEADERS[name]}")
        return "error", "include", f"<{name}> is not a C++17 standard header"
    resolved = (header.parent / name).resolve()
    if resolved.is_file() and resolved.is_relative_to(core):
        return None
    return "error", "include", f'"{name}" does not resolve to a header inside the core folder'


def findings_in(header: Path, core: Path) -> list[tuple[int, str, str, str]]:
    """(line, severity, rule, message) for each problem in one header."""
    no_comments, bare = strip(header.read_text())
    found = []
    for match in INCLUDE.finditer(no_comments):
        problem = include_problem(*match.groups(), header, core)
        if problem:
            found.append((line_of(no_comments, match.start(2)), *problem))
    for pattern, rule, what in NAMES:
        for match in pattern.finditer(bare):
            found.append((line_of(bare, match.start()), "error", rule, f"{what} in the core: {match.group()}"))
    return sorted(found)


HEADER_SUFFIXES = {".h", ".hpp"}
SOURCE_SUFFIXES = {".cpp", ".cc", ".cxx"}


def files_in(path: Path, suffixes: set[str]) -> list[Path]:
    """`path` itself if its suffix is one of `suffixes`, or every such file under the folder."""
    if path.is_file():
        return [path] if path.suffix in suffixes else []
    return sorted(p for p in path.rglob("*") if p.suffix in suffixes and p.is_file())


def findings_under(path: Path) -> Iterator[tuple[Path, int, str, str, str]]:
    """Yield (file, line, severity, rule, message) for every problem in the core at `path`.

    The core folder is `path` itself, or the folder holding it when `path` is a file.
    """
    core = (path.parent if path.is_file() else path).resolve()
    for header in files_in(path, HEADER_SUFFIXES):
        for lineno, severity, rule, message in findings_in(header, core):
            yield header, lineno, severity, rule, message
    for source in files_in(path, SOURCE_SUFFIXES):
        yield source, 1, "error", "header-only", "the core must be header-only; move this code into a header"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="check_core_purity.py",
        description="Check that a portable DSP core is header-only, standard-library-only C++17.",
    )
    parser.add_argument("paths", nargs="+", type=Path, help="core folders or header files")
    args = parser.parse_args(argv)
    missing = [str(path) for path in args.paths if not path.exists()]
    if missing:
        parser.error(f"no such path: {', '.join(missing)}")
    if not any(files_in(path, HEADER_SUFFIXES | SOURCE_SUFFIXES) for path in args.paths):
        parser.error("no headers (.h, .hpp) or source files (.cpp, .cc, .cxx) found")
    status = 0
    for path in args.paths:
        for file, lineno, severity, rule, message in findings_under(path):
            print(f"{file}:{lineno}: {severity}: {rule}: {message}")
            if severity == "error":
                status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
