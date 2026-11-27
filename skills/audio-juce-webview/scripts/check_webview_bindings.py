#!/usr/bin/env python3
"""Check that a JUCE WebView editor's relays and its page's state requests name each other.

Relays are constructions of juce::WebSliderRelay, WebToggleButtonRelay or
WebComboBoxRelay in C++ files (.h, .hpp, .cpp, .cc, .cxx): a declaration with a
brace or parenthesis initialiser, a temporary, or a make_unique of the class. A
relay's name is the string literal passed to it. State requests are calls to
getSliderState, getToggleState or getComboBoxState in page files (.html, .htm, .js,
.mjs, .ts, .tsx, .jsx), called bare, through a namespace import or through an import
renamed with `as`. A state's name is the string literal passed to it. Comments and
other string literals are ignored; in HTML, only the contents of script elements are
read. Functions defined with a state function's name aren't requests.

Each relay class pairs with one state function: WebSliderRelay with getSliderState,
WebToggleButtonRelay with getToggleState, WebComboBoxRelay with getComboBoxState.

Reported as errors:
- relay-name: a relay whose name no state request has, and a state request whose
  name no relay has
- relay-type: a state request whose name only relays of another class have, at the
  request (a type mismatch still counts as a name match)

Reported as a warning (rule relay-name): a relay class whose names one side computes
(a relay constructed, or a state requested, with anything but a string literal). It
is reported once per class, at the first computed site, and no unmatched names of
that class are reported on either side. Warnings alone exit 0.

Reported as errors (rule module): JUCE's interop library loaded by a script element
without type="module"; a name the library doesn't export, imported from it or called
through its namespace import (checked against JUCE 9.0.6's export list, carried here);
and a state function called through window.__JUCE__. A specifier names the library
when it resolves to a library file, names the npm package @juce-framework/webview, or
is the one the page imports a state function from. A library file is recognised by
content: it defines the three state functions, or sets up
window.__JUCE__.initialisationData (JUCE 8's check_native_interop.js). Library files
are not scanned as page code.

Folders are searched recursively, leaving out node_modules, .git, _deps and any
folder that holds a CMakeCache.txt.

    check_webview_bindings.py <editor sources and UI folders or files>...

Prints `file:line: severity: rule: message` per finding. Exit 0 = no errors,
1 = errors, 2 = usage error (a missing path, or no C++ files or no page files found).
"""
import argparse
import os
import re
import sys
from pathlib import Path

CPP_SUFFIXES = (".h", ".hpp", ".cpp", ".cc", ".cxx")
PAGE_SUFFIXES = (".html", ".htm", ".js", ".mjs", ".ts", ".tsx", ".jsx")
SKIPPED_FOLDERS = {"node_modules", ".git", "_deps"}

RELAY_CLASS = re.compile(r"\bWeb(?:Slider|ToggleButton|ComboBox)Relay\b")
MAKE_UNIQUE_BEFORE = re.compile(r"make_unique\s*<\s*(?:juce\s*::\s*)?$")
AFTER_MAKE_UNIQUE = re.compile(r"\s*>\s*[{(]")
DECLARATOR = re.compile(r"\s*(?:[A-Za-z_]\w*\s*)?[{(]")
NEXT_DECLARATOR = re.compile(r"\s*,\s*[A-Za-z_]\w*\s*[{(]")
STATE_FUNCTIONS = ("getSliderState", "getToggleState", "getComboBoxState")
STATE_FUNCTION_OF = {"WebSliderRelay": "getSliderState",
                     "WebToggleButtonRelay": "getToggleState",
                     "WebComboBoxRelay": "getComboBoxState"}
RELAY_CLASS_OF = {function: relay_class for relay_class, function in STATE_FUNCTION_OF.items()}
LITERAL = re.compile(r"""(["'`])[^"'`\n]*\1""")
DEFINITION_BEFORE = re.compile(r"\bfunction\s*$")
BODY_AFTER = re.compile(r"\s*\{")
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


def closing(code, start):
    """The offset of the bracket that closes the one at `start`, in masked code."""
    depth = 0
    for i in range(start, len(code)):
        if code[i] in "([{":
            depth += 1
        elif code[i] in ")]}":
            depth -= 1
            if depth == 0:
                return i
    return len(code)


def argument(text, code, start, end):
    """(name, offset) for the argument between `start` and `end`: a string literal's
    contents and offset, (None, offset) for anything else, or None when it is empty."""
    raw = code[start:end]
    if not raw.strip():
        return None
    offset = start + len(raw) - len(raw.lstrip())
    source = text[offset:offset + len(raw.strip())]
    if LITERAL.fullmatch(raw.strip()) and not (source[0] == "`" and "${" in source):
        return source[1:-1], offset + 1
    return None, offset


def relay_names(path):
    """(name, path, line, class) for each relay construction in a C++ file.

    `name` is None when the argument isn't a string literal. A construction is a
    declaration (one or more declarators with a brace or parenthesis initialiser), a
    temporary, or a make_unique of the class; other mentions of the class are types."""
    text = path.read_text()
    code = mask(text, "\"'")
    found = []
    for relay in RELAY_CLASS.finditer(code):
        made = MAKE_UNIQUE_BEFORE.search(code[max(0, relay.start() - 64):relay.start()])
        opening = (AFTER_MAKE_UNIQUE if made else DECLARATOR).match(code, relay.end())
        while opening:
            end = closing(code, opening.end() - 1)
            request = argument(text, code, opening.end(), end)
            if request:
                name, offset = request
                found.append((name, path, line_of(text, offset), relay.group()))
            opening = None if made else NEXT_DECLARATOR.match(code, end + 1)
    return found


def state_names(path):
    """(name, path, line, function) for each state request in a page file.

    `name` is None when the argument isn't a string literal. `function` is the state
    function's own name, even when it was called through an alias. Definitions of
    functions with these names aren't requests."""
    text = path.read_text()
    if path.suffix in {".html", ".htm"}:
        text = scripts_only(text)
    code = mask(text, "\"'`")
    functions = {name: name for name in STATE_FUNCTIONS}
    functions.update({alias.group(2): alias.group(1) for alias in ALIAS.finditer(code)})
    call = re.compile(r"(?<![\w$])(" + "|".join(map(re.escape, functions)) + r")\s*\(")
    found = []
    for hit in call.finditer(code):
        end = closing(code, hit.end() - 1)
        before = code[max(0, hit.start() - 64):hit.start()]
        if DEFINITION_BEFORE.search(before) or BODY_AFTER.match(code, end + 1):
            continue
        request = argument(text, code, hit.end(), end)
        if request:
            name, offset = request
            found.append((name, path, line_of(text, offset), functions[hit.group(1)]))
    return found


def computed_warnings(relays, states):
    """One relay-name warning per relay class whose names either side computes, at the
    first place they are computed (the C++ side first), and the set of those classes."""
    warnings, computed = [], set()
    sites = ([(relay_class, path, line, "C++") for name, path, line, relay_class in relays
              if name is None]
             + [(RELAY_CLASS_OF[function], path, line, "page")
                for name, path, line, function in states if name is None])
    for relay_class, path, line, side in sites:
        if relay_class in computed:
            continue
        computed.add(relay_class)
        function = STATE_FUNCTION_OF[relay_class]
        ours, theirs = (relay_class, function) if side == "C++" else (function, relay_class)
        warnings.append(f"{path}:{line}: warning: relay-name: {ours} names are computed in"
                        f" the {side}, so {theirs} names can't be matched")
    return warnings, computed


def unmatched(found, other, message):
    """A relay-name error for each name in `found` that `other` doesn't have."""
    known = {name for name, *_ in other}
    return [f"{path}:{line}: error: relay-name: {message.format(name)}"
            for name, path, line, _ in found if name not in known]


def wrong_types(states, relays):
    """A relay-type error for each state whose name only relays of other classes have."""
    classes = {}
    for name, _, _, relay_class in relays:
        classes.setdefault(name, set()).add(relay_class)
    report = []
    for name, path, line, function in states:
        relay_class = min(classes.get(name, ()), default=None)
        if relay_class and function not in {STATE_FUNCTION_OF[c] for c in classes[name]}:
            report.append(f'{path}:{line}: error: relay-type: state "{name}" is requested with'
                          f" {function}, but its relay is a {relay_class}"
                          f" (use {STATE_FUNCTION_OF[relay_class]})")
    return report


def source_files(path):
    """Every file under `path`, leaving out dependency and CMake build folders."""
    if path.is_file():
        return [path]
    if path.name in SKIPPED_FOLDERS or (path / "CMakeCache.txt").exists():
        return []
    return [f for child in sorted(path.iterdir()) for f in source_files(child)]


# The module rule: how the page loads JUCE's interop library.

STATE_DEFINITION = r"\b(?:function\s+{0}\s*\(|(?:const|let|var)\s+{0}\s*=)"
NATIVE_INTEROP = re.compile(r"__JUCE__\s*\.\s*initialisationData\s*=(?!=)")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
ATTRIBUTE = re.compile(r"""([^\s=/>]+)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s>]+))?""")
IMPORT = re.compile(r"""\bimport\s+(?:type\s+)?([\w$\s{},*]*?)\s*\bfrom\s*(["'])""")
IMPORTED_NAME = re.compile(r"([\w$]+)(?:\s+as\s+[\w$]+)?")
NAMESPACE = re.compile(r"\*\s*as\s+([\w$]+)")
NPM_PACKAGE = "@juce-framework/webview"
GLOBAL_STATE_CALL = re.compile(r"(?<![\w$])__JUCE__\s*(?:\??\.\s*[\w$]+\s*)*?\??\.\s*("
                               + "|".join(STATE_FUNCTIONS) + r")\s*\(")

# What JUCE 9.0.6's interop library exports: the export list at the end of
# modules/juce_gui_extra/native/typescript/webview-interop/dist/index.js
# (npm package @juce-framework/webview 1.0.0, built from src/index.ts).
LIBRARY_EXPORTS = {
    "getNativeFunction", "getSliderState", "getToggleState", "getComboBoxState",
    "getBackendResourceAddress", "ControlParameterIndexUpdater",
}


def is_interop_library(path):
    """Whether a page file is part of JUCE's interop library: it defines the state
    functions (JUCE 8's index.js, JUCE 9's built index.js) or sets up
    window.__JUCE__.initialisationData (JUCE 8's check_native_interop.js)."""
    code = mask(path.read_text(), "\"'`")
    return bool(NATIVE_INTEROP.search(code)) or all(
        re.search(STATE_DEFINITION.format(name), code) for name in STATE_FUNCTIONS)


def specifier_key(page, specifier):
    """What a script src or import specifier in `page` points at: the npm package's
    name, or a normalised path."""
    if specifier == NPM_PACKAGE or specifier.startswith(NPM_PACKAGE + "/"):
        return NPM_PACKAGE
    return os.path.normpath(os.path.abspath(page.parent / specifier.lstrip("/")))


def file_key(path):
    """The key specifier_key gives a specifier that resolves to `path`."""
    return os.path.normpath(os.path.abspath(path))


def script_sources(path):
    """(src, has type="module", offset) for each script element with a src in an HTML file."""
    html = HTML_COMMENT.sub(lambda comment: blank(comment.group()), path.read_text())
    found = []
    for element in SCRIPT_ELEMENT.finditer(html):
        attributes = {name.lower(): (value or "").strip("\"'")
                      for name, value in ATTRIBUTE.findall(element.group(1)[len("<script"):])}
        if "src" in attributes:
            is_module = attributes.get("type", "").lower() == "module"
            found.append((attributes["src"], is_module, element.start()))
    return found


def page_code(path):
    """(text, code) of a page file: its text, and that text masked as in state_names."""
    text = path.read_text()
    if path.suffix in {".html", ".htm"}:
        text = scripts_only(text)
    return text, mask(text, "\"'`")


def imports(path):
    """(key, [(name, offset)]) for each static import in a page file. The names are
    those it imports by name and those the file calls through its namespace import."""
    text, code = page_code(path)
    found = []
    for hit in IMPORT.finditer(code):
        end = code.find(hit.group(2), hit.end())
        brace = re.search(r"\{([^}]*)\}", hit.group(1))
        names = ([(name.group(1), hit.start(1) + brace.start(1) + name.start(1))
                  for name in IMPORTED_NAME.finditer(brace.group(1))] if brace else [])
        namespace = NAMESPACE.search(hit.group(1))
        if namespace:
            call = re.compile(r"(?<![\w$.])" + re.escape(namespace.group(1))
                              + r"\s*\??\.\s*([\w$]+)\s*\(")
            names += [(member.group(1), member.start(1)) for member in call.finditer(code)]
        found.append((specifier_key(path, text[hit.end():end]), names))
    return found


def module_findings(page_files, libraries):
    """Module errors: the interop library loaded without type="module", names used
    from it that it doesn't export, and state functions called through window.__JUCE__."""
    page_imports = {path: imports(path) for path in page_files}
    library_keys = ({NPM_PACKAGE} | {file_key(path) for path in libraries}
                    | {key for file_imports in page_imports.values() for key, names in file_imports
                       if any(name in STATE_FUNCTIONS for name, _ in names)})
    report = []
    for path in page_files:
        text, code = page_code(path)
        found = [(offset, f'"{name}" is not exported by JUCE\'s interop library')
                 for key, names in page_imports[path] if key in library_keys
                 for name, offset in names if name not in LIBRARY_EXPORTS]
        found += [(hit.start(1), f"{hit.group(1)} is called through window.__JUCE__; "
                   "import it from JUCE's interop library")
                  for hit in GLOBAL_STATE_CALL.finditer(code)]
        if path.suffix in {".html", ".htm"}:
            found += [(offset, f'JUCE\'s interop library "{src}" is loaded without '
                       'type="module"')
                      for src, is_module, offset in script_sources(path)
                      if specifier_key(path, src) in library_keys and not is_module]
        report += [f"{path}:{line_of(text, offset)}: error: module: {message}"
                   for offset, message in sorted(found)]
    return report


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
    libraries = [path for path in page_files if is_interop_library(path)]
    page_files = [path for path in page_files if path not in libraries]
    relays = [r for path in cpp_files for r in relay_names(path)]
    states = [s for path in page_files for s in state_names(path)]
    warnings, computed = computed_warnings(relays, states)
    relays = [r for r in relays if r[0] is not None]
    states = [s for s in states if s[0] is not None]
    errors = (unmatched([r for r in relays if r[3] not in computed], states,
                        'relay "{}" has no matching state in the page')
              + unmatched([s for s in states if RELAY_CLASS_OF[s[3]] not in computed], relays,
                          'state "{}" has no matching relay in the C++')
              + wrong_types(states, relays)
              + module_findings(page_files, libraries))
    for finding in warnings + errors:
        print(finding)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
