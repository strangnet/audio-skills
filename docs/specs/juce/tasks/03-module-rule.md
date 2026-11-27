# 03: The checker checks how the page loads JUCE's library

Status: done
Spec: [juce](../../juce.md)
Blocked by: 01

## Delivers
The `module` rule: the interop library must be loaded as an ES module, only its real exports may be imported or called through its namespace, and state functions must not be called through `window.__JUCE__`. The library is recognised by content, so a vendored copy (including JUCE 8's separate native-interop file) isn't scanned as page code.

## Scenarios
- Checker: the library loaded without `type="module"` → `module` error
- Checker: a name the library doesn't export, imported or called through its namespace → `module` error
- Checker: a state function called through `window.__JUCE__` → `module` error; other uses not reported
- Checker: a copy of JUCE's library inside the UI folder → not scanned as page code
