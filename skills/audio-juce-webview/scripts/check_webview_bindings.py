#!/usr/bin/env python3
"""Check that a JUCE WebView editor's relays and its page's state requests name each other.

Relays are constructions of juce::WebSliderRelay, WebToggleButtonRelay or
WebComboBoxRelay in C++ files (.h, .hpp, .cpp, .cc, .cxx): a declaration with a
brace or parenthesis initialiser, or a make_unique of the class. A relay's name is
the string literal passed to it. State requests are calls to getSliderState,
getToggleState or getComboBoxState in page files (.html, .htm, .js, .mjs), called
bare, through a namespace import or through an import renamed with `as`. A state's
name is the string literal passed to it. Comments and other string literals are
ignored; in HTML, only the contents of script elements are read.

Reported as errors (rule relay-name): a relay whose name no state request has, and
a state request whose name no relay has.

Folders are searched recursively, leaving out node_modules, .git, _deps and any
folder that holds a CMakeCache.txt.

    check_webview_bindings.py <editor sources and UI folders or files>...

Prints `file:line: severity: rule: message` per finding. Exit 0 = no errors,
1 = errors, 2 = usage error (a missing path, or no C++ files or no page files found).
"""
import argparse
import re
import sys
from pathlib import Path

CPP_SUFFIXES = (".h", ".hpp", ".cpp", ".cc", ".cxx")
PAGE_SUFFIXES = (".html", ".htm", ".js", ".mjs")
SKIPPED_FOLDERS = {"node_modules", ".git", "_deps"}

RELAY_CLASS = re.compile(r"\bWeb(?:Slider|ToggleButton|ComboBox)Relay\b")
LITERAL_ARGUMENT = re.compile(r'[{(]\s*"([^"\n]*)"')
STATE_FUNCTIONS = ("getSliderState", "getToggleState", "getComboBoxState")
ALIAS = re.compile(r"\b(" + "|".join(STATE_FUNCTIONS) + r")\s+as\s+([A-Za-z_$][\w$]*)")
SCRIPT_ELEMENT = re.compile(r"(<script\b[^>]*>)(.*?)</script\s*>", re.IGNORECASE | re.DOTALL)


def blank(text):
    """Every character but newlines replaced with a space, so offsets and lines survive."""
    return re.sub(r"[^\n]", " ", text)


def mask(text, quotes):
    """`text` with comments blanked and the contents of string literals blanked.

    The quote characters themselves stay, so a pattern can find a literal in the
    masked text and read its contents from the original at the same offsets."""
    out = []
    i = 0
    while i < len(text):
        if text.startswith("//", i):
            end = text.find("\n", i)
            end = len(text) if end < 0 else end
            out.append(blank(text[i:end]))
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = len(text) if end < 0 else end + 2
            out.append(blank(text[i:end]))
        elif text[i] in quotes:
            end = i + 1
            while end < len(text) and text[end] not in (text[i], "\n"):
                end += 2 if text[end] == "\\" else 1
            end = min(end, len(text) - 1)
            out.append(text[i] + blank(text[i + 1:end]) + text[end])
            end += 1
        else:
            end = i + 1
            out.append(text[i])
        i = end
    return "".join(out)


def scripts_only(html):
    """`html` with everything outside `<script>` elements blanked."""
    out, done = [], 0
    for element in SCRIPT_ELEMENT.finditer(html):
        start, end = element.span(2)
        out += [blank(html[done:start]), html[start:end]]
        done = end
    return "".join(out) + blank(html[done:])


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def relay_names(path):
    """(name, path, line) for each literal name given to a relay class in a C++ file."""
    text = path.read_text()
    code = mask(text, "\"'")
    found = []
    for relay in RELAY_CLASS.finditer(code):
        end = code.find(";", relay.end())
        declaration_end = len(code) if end < 0 else end
        for hit in LITERAL_ARGUMENT.finditer(code, relay.end(), declaration_end):
            start, stop = hit.span(1)
            found.append((text[start:stop], path, line_of(text, start)))
    return found


def state_names(path):
    """(name, path, line) for each literal name given to a state function in a page file."""
    text = path.read_text()
    if path.suffix in {".html", ".htm"}:
        text = scripts_only(text)
    code = mask(text, "\"'`")
    functions = set(STATE_FUNCTIONS) | {alias.group(2) for alias in ALIAS.finditer(code)}
    call = re.compile(r"(?<![\w$])(?:" + "|".join(map(re.escape, functions))
                      + r""")\s*\(\s*(["'`])([^"'`\n]*)\1""")
    return [(text[hit.start(2):hit.end(2)], path, line_of(text, hit.start(2)))
            for hit in call.finditer(code)]


def unmatched(found, other, message):
    """A relay-name error for each name in `found` that `other` doesn't have."""
    known = {name for name, _, _ in other}
    return [f"{path}:{line}: error: relay-name: {message.format(name)}"
            for name, path, line in found if name not in known]


def source_files(path):
    """Every file under `path`, leaving out dependency and CMake build folders."""
    if path.is_file():
        return [path]
    if path.name in SKIPPED_FOLDERS or (path / "CMakeCache.txt").exists():
        return []
    return [f for child in sorted(path.iterdir()) for f in source_files(child)]


def main(argv):
    parser = argparse.ArgumentParser(
        description="Check that a JUCE WebView editor's relays and its page's states agree.")
    parser.add_argument("paths", nargs="+", type=Path, help="editor sources and UI folders")
    args = parser.parse_args(argv)
    for path in args.paths:
        if not path.exists():
            parser.error(f"no such file or folder: {path}")
    files = [path for root in args.paths for path in source_files(root)]
    cpp_files = [path for path in files if path.suffix in CPP_SUFFIXES]
    page_files = [path for path in files if path.suffix in PAGE_SUFFIXES]
    if not cpp_files:
        parser.error(f"no C++ files ({', '.join(CPP_SUFFIXES)}) found")
    if not page_files:
        parser.error(f"no page files ({', '.join(PAGE_SUFFIXES)}) found")
    relays = [r for path in cpp_files for r in relay_names(path)]
    states = [s for path in page_files for s in state_names(path)]
    report = (unmatched(relays, states, 'relay "{}" has no matching state in the page')
              + unmatched(states, relays, 'state "{}" has no matching relay in the C++'))
    for finding in report:
        print(finding)
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
