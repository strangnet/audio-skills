---
name: audio-juce-webview
description: WebView editor know-how for JUCE 9 audio plugins (VST3, AU, CLAP) on macOS, covering serving the page from inside the plugin through the resource provider, JUCE's JavaScript interop library, relays and attachments, gestures, what fails silently, and a binding checker script that compares the relays the C++ creates with the states the page requests. Use when building, wiring up or debugging a JUCE WebView editor or its page; when the WebView shows a blank page, knobs don't move or don't follow automation, or automation isn't recorded; or when adding, renaming or removing a relay or a `getSliderState`, `getToggleState` or `getComboBoxState` call. Not for Component-based JUCE editors, for the processor, CMake and formats (use `audio-juce`), or for an ordinary web page or web app. Not for work inside an Akai MPC SDK checkout, which Akai's own `mpc-plugin-*` skills cover (use those there). Not for Claude Code or Cowork plugins.
---

# Audio JUCE WebView

A JUCE WebView editor is two programs that only meet by name: C++ relays on one side, JavaScript states on the other. When the names or types disagree, nothing fails loudly. The control just doesn't move. This skill covers JUCE 9.0.6 on macOS.

## The binding checker

`scripts/check_webview_bindings.py` (Python 3, standard library only) reads the editor's C++ sources and its UI folder:

```bash
python3 scripts/check_webview_bindings.py <editor sources> <UI folder>...
```

Run it with this skill's folder as the base. It finds each relay construction's literal name and each state request's literal name, and reports, as `file:line: severity: rule: message`:
- `relay-name`: a relay whose name no state request has, or a state request whose name no relay has

It ignores comments, other strings and the page's visible text, and skips `node_modules`, `.git`, `_deps` and CMake build folders. Exit 0 means no errors, 1 means errors, and 2 is a usage error.
