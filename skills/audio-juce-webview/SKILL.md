---
name: audio-juce-webview
description: WebView editor know-how for JUCE 9 audio plugins (VST3, AU, CLAP) on macOS, covering serving the page from inside the plugin through the resource provider, JUCE's JavaScript interop library, relays and attachments, gestures, what fails silently, and a binding checker script that compares the relays the C++ creates with the states the page requests. Use when building, wiring up or debugging a JUCE WebView editor or its page; when the WebView shows a blank page, knobs don't move or don't follow automation, or automation isn't recorded; or when adding, renaming or removing a relay or a `getSliderState`, `getToggleState` or `getComboBoxState` call. Not for Component-based JUCE editors, for the processor, CMake and formats (use `audio-juce`), or for an ordinary web page or web app. Not for work inside an Akai MPC SDK checkout, which Akai's own `mpc-plugin-*` skills cover (use those there). Not for Claude Code or Cowork plugins.
---

# Audio JUCE WebView

A JUCE WebView editor is two programs that only meet by name: C++ relays on one side, JavaScript states on the other. When the names or types disagree, nothing fails loudly. The control just doesn't move. This skill covers JUCE 9.0.6 on macOS; each reference names the JUCE file its facts come from. **Windows (WebView2) isn't covered yet**, and this skill gives no Windows advice. The processor, CMake, formats and the editor's lifecycle belong to the `audio-juce` skill.

## Rules

- **Serve the page through the resource provider and its root URL, not a file URL.** Register `Options::withResourceProvider(...)` and call `goToURL(WebBrowserComponent::getResourceProviderRoot())`. The root arrives at the provider as `/`; every other file as `/path`. A file URL needs the files installed at a known path, and the macOS web view blocks the page's sibling files by default. See [references/serving-the-page.md](references/serving-the-page.md).
- **Map each URL to its embedded file and MIME type explicitly.** `juce_add_binary_data` names each file by its file name alone (`ui/juce/index.js` becomes `index_js`), so write a table: URL path, data, size, MIME type. A module script served without a JavaScript MIME type (`text/javascript`) doesn't run.
- **Take JUCE's interop library from the same JUCE version**: `modules/juce_gui_extra/native/typescript/webview-interop/dist/index.js` from the checkout (embed it straight from `${JUCE_DIR}`), or the npm package `@juce-framework/webview` at the version in that folder's `package.json`. JUCE 9 compares the two versions at run time. Its `index.js` bundles the native-interop check, so the page loads that one file and nothing else from JUCE.
- **Load the library as an ES module and import from it**: `<script type="module">` and `import * as Juce from "./juce/index.js"`. The state functions aren't on `window.__JUCE__`.
- **Construct each relay with its name and register it with the browser options**: `juce::WebSliderRelay driveRelay { "drive" };` and `.withOptionsFrom (driveRelay)`. See [references/relays-and-attachments.md](references/relays-and-attachments.md).
- **Declare each relay before the browser and each attachment after its relay.** Relays, browser, then attachments is the usual order: the relay outlives the browser that holds its options, and the attachment is destroyed before its relay. In JUCE 9.0.6 an attachment declared before the browser is also safe. Plain members work; `std::unique_ptr` is optional.
- **Match the JavaScript state type to the relay type**: `WebSliderRelay` with `getSliderState` (float and int parameters), `WebToggleButtonRelay` with `getToggleState` (bool), `WebComboBoxRelay` with `getComboBoxState` (choice). Attach each with the matching `Web*ParameterAttachment (parameter, relay)`; the undo manager is an optional third argument.
- **Value-changed listeners take no arguments.** Read the value inside the listener: `state.valueChangedEvent.addListener(() => draw(state.getNormalisedValue()))`.
- **Wrap every user edit of a slider in `sliderDragStarted()` and `sliderDragEnded()`**, so the host records one gesture. Toggle and combo-box attachments wrap each change in a gesture themselves.
- **Treat "unknown to the backend" as the bug.** A state name the C++ side doesn't know (wrong name, wrong type, relay not registered) only logs that console warning. It's the usual silent cause of a frozen control. In a debug build, right-click the page and choose Inspect Element to see the console.
- **Enable native integration, only for the plugin's own content, and keep navigation on the plugin's page.** Relays need `withNativeIntegrationEnabled()` (they don't turn it on; `withNativeFunction` does). Override `pageAboutToLoad` to allow only the provider's root. See [references/native-functions-events-and-navigation.md](references/native-functions-events-and-navigation.md).
- **Native function and event callbacks run on the message thread. Send events to the page only after its first load** (`pageFinishedLoading`), from the message thread, never from the audio thread. Meters: the audio thread writes atomics or a FIFO, and a timer on the editor sends them (real-time rules: `audio-dsp`).
- **Run the binding checker** after adding, renaming or removing a relay or a state request.

## The binding checker

`scripts/check_webview_bindings.py` (Python 3, standard library only) reads the editor's C++ sources and its UI folder:

```bash
python3 scripts/check_webview_bindings.py <editor sources> <UI folder>...
```

Run it with this skill's folder as the base. It reads pages in `.html`, `.htm`, `.js`, `.mjs`, `.ts`, `.tsx` and `.jsx`. It finds each relay construction's name and each state request's name, and reports, as `file:line: severity: rule: message`:
- `relay-name` error: a relay whose name no state request has, or a state request whose name no relay has
- `relay-type` error: a state requested with the wrong function for its relay. `WebSliderRelay` pairs with `getSliderState`, `WebToggleButtonRelay` with `getToggleState`, `WebComboBoxRelay` with `getComboBoxState`
- `relay-name` warning: names of one relay class that aren't string literals on one side (a relay built from a parameter table, `getSliderState(id)` in a loop). It comes once per class, and that class's unmatched names go unreported, since they can't be matched
- `module` error: JUCE's interop library loaded without `type="module"`; a name the library doesn't export, imported from it or called through its namespace (`Juce.getSlidrState`); a state function called through `window.__JUCE__`

The checker carries JUCE 9.0.6's export list (`getNativeFunction`, `getSliderState`, `getToggleState`, `getComboBoxState`, `getBackendResourceAddress`, `ControlParameterIndexUpdater`, from `modules/juce_gui_extra/native/typescript/webview-interop/dist/index.js`). It recognises the library by content, so a copy in the UI folder (JUCE 8's `check_native_interop.js` too) isn't read as page code. It ignores comments, other strings and the page's visible text, and skips `node_modules`, `.git`, `_deps` and CMake build folders. Exit 0 means no errors (warnings alone pass), 1 means errors, and 2 is a usage error.

### What the checker can't see

A clean run doesn't prove the editor works. Check these by reading the code:
- each relay passed to `withOptionsFrom`, and `withNativeIntegrationEnabled()` on the same options
- member declaration order: relays, browser, attachments
- `goToURL(getResourceProviderRoot())`, and the provider answering `/`
- every file the page references served by the provider, with its MIME type
- parameter ids passed to the attachments (often built at run time)
- native function names and event ids on both sides
- the gesture calls around slider edits
- modules beyond the page's own files (a bundler's dependencies)

## References

Read only what the task needs:

- [references/serving-the-page.md](references/serving-the-page.md): the resource provider and its root, the URL map and MIME types, binary data, file URLs, the interop library and its version check, ES modules, a dev server, the hidden page.
- [references/relays-and-attachments.md](references/relays-and-attachments.md): the three relay, attachment and state pairs, registration, native integration, member order, the page's state API, gestures, ranges and choices, the control under the mouse.
- [references/native-functions-events-and-navigation.md](references/native-functions-events-and-navigation.md): native integration and navigation, native functions, events both ways, feeding meters, the page's console.
- [references/troubleshooting.md](references/troubleshooting.md): blank page, frozen knobs, controls that ignore automation, automation not recorded, wrong values, crashes on close, and the JUCE 9.0.6 facts that older advice gets wrong.

## Pitfalls

- A provider that answers `/index.html` but not `/`: blank page.
- `<script src="juce/index.js">` without `type="module"`, or `window.__JUCE__.getSliderState(...)`: the page shows, every control is frozen.
- `"Drive"` in C++ and `"drive"` in the page, or a toggle read with `getSliderState`: one console warning, one frozen control.
- Relays registered, native integration never enabled: edits never reach C++.
- `valueChangedEvent.addListener((v) => draw(v))`: draws `undefined` on every automation change.
- `setNormalisedValue` on every input event with no drag start and end: the sound changes but the host records no automation.
- A relay declared after the browser: a crash when the editor closes.
- The library copied from another JUCE version or an npm release that doesn't match: a version warning, and behaviour that drifts.
- A slider on a parameter with custom range functions or a symmetric skew: the page and the host disagree about the value.
- Testing in a host that still loads an old installed bundle (see `audio-juce`).

## Sources

JUCE 9.0.6, paraphrased: `modules/juce_gui_extra/misc/juce_WebBrowserComponent.h` and `.cpp`, `juce_WebControlRelays.h` and `.cpp`, `juce_WebControlParameterIndexReceiver.h`, `modules/juce_gui_extra/native/juce_WebBrowserComponent_mac.mm`, `modules/juce_audio_processors/utilities/juce_ParameterAttachments.h` and `.cpp`, `modules/juce_gui_extra/native/typescript/webview-interop/` (`package.json`, `src/`, `dist/index.js`), `extras/Build/CMake/JUCEModuleSupport.cmake`, `docs/CMake API.md`, and `examples/Plugins/WebViewPluginDemo.h` with its GUI. Each reference lists the exact sources for its facts. Troubleshooting patterns are curated from the Plugin Freedom System's notes and kept only where 9.0.6 confirms them.
