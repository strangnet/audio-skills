# 01: The binding checker matches relay names between the C++ and the page

Status: done
Spec: [juce](../../juce.md)
Blocked by: none

## Delivers
The `audio-juce-webview` skill folder exists, with its final frontmatter and a short `SKILL.md` that names the binding checker. The checker reads an editor's C++ sources and its UI folder, finds each relay construction's literal name and each page state request's literal name, and reports names that appear on only one side. It runs on the tilt-EQ example and passes; a pytest test runs it there in CI. This tests the spec's riskiest assumption first, against the example and two Plugin Freedom System editors.

## Scenarios
- Checker: an editor whose names, types and library loading all agree → no findings (relay names only, at this stage)
- Checker: a C++ relay with no matching state, or a state with no matching relay → `relay-name` errors
- Checker: names, `type="module"` or state calls only in comments, non-code strings or visible text → not counted
- Checker: dependency and build folders under a parent folder → not read
- Checker: a missing path, or no C++ files or no page files → usage error
- Testing seam: the binding checker on the real example → pytest in CI
