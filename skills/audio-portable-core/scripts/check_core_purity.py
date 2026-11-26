#!/usr/bin/env python3
"""Check that a portable DSP core is pure: header-only C++17 using only the standard library.

Comments and string literals are stripped before matching. Allowed includes are the
C++17 standard library headers (with the C compatibility headers in their <cname>
form) and quoted includes that resolve to a file inside the core folder. Reported as
errors: any other include, any juce:: or mpc:: name, any JUCE_ macro (whatever the
includes), and any .cpp file in the core.

    check_core_purity.py <core folder>...

Prints `file:line: severity: rule: message` per finding. Exit 0 = no errors,
1 = errors, 2 = usage error (no path, a missing path, or no headers found).
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


def include_problem(kind: str, name: str, header: Path, core: Path) -> str | None:
    if kind == "<":
        return None if name in STANDARD_HEADERS else f"<{name}> is not a C++17 standard header"
    resolved = (header.parent / name).resolve()
    if resolved.is_file() and resolved.is_relative_to(core):
        return None
    return f'"{name}" does not resolve to a header inside the core folder'


def findings_in(header: Path, core: Path) -> list[tuple[int, str, str]]:
    no_comments, bare = strip(header.read_text())
    found = []
    for match in INCLUDE.finditer(no_comments):
        problem = include_problem(*match.groups(), header, core)
        if problem:
            found.append((line_of(no_comments, match.start(2)), "include", problem))
    for pattern, rule, what in NAMES:
        for match in pattern.finditer(bare):
            found.append((line_of(bare, match.start()), rule, f"{what} in the core: {match.group()}"))
    return sorted(found)


def files_in(path: Path, suffix: str) -> list[Path]:
    """`path` itself if it is a file with `suffix`, or every such file under the folder."""
    if path.is_file():
        return [path] if path.suffix == suffix else []
    return sorted(path.glob(f"**/*{suffix}"))


def findings_under(path: Path) -> Iterator[tuple[Path, int, str, str]]:
    """Yield (file, line, rule, message) for every problem in the core at `path`.

    The core folder is `path` itself, or the folder holding it when `path` is a file.
    """
    core = (path.parent if path.is_file() else path).resolve()
    for header in files_in(path, ".h"):
        for lineno, rule, message in findings_in(header, core):
            yield header, lineno, rule, message
    for source in files_in(path, ".cpp"):
        yield source, 1, "header-only", "the core must be header-only; move this code into a header"


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
    if not any(files_in(path, ".h") for path in args.paths):
        parser.error("no headers (.h) found")
    status = 0
    for path in args.paths:
        for file, lineno, rule, message in findings_under(path):
            print(f"{file}:{lineno}: error: {rule}: {message}")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
