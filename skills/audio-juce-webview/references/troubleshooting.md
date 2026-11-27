# Troubleshooting a WebView editor

Symptoms first, with their usual causes in the order worth checking. Facts checked against JUCE 9.0.6 on macOS; the other references cite the sources. Open the page's console first (debug build, right-click, Inspect Element): most of these failures show up there and nowhere else.

Before chasing any of them, make sure the host loaded the build you just made. Hosts load installed bundles and cache their scans (see `audio-juce`).

## A blank page

1. **The root isn't served.** `goToURL(getResourceProviderRoot())` makes the provider receive `/`. A provider that only answers `/index.html`, or compares against a path without the leading slash, returns nothing, and the web view gets a 404.
2. **`goToURL` was never called,** or was called with a `file:` URL to a file that isn't installed at that path on this machine.
3. **`index.html` is served with the wrong MIME type.** As `text/plain` the page shows as text; as an empty type it may not render at all.
4. **`pageAboutToLoad` rejects the root,** for example by comparing against a hard-coded string that isn't this platform's root.
5. **The browser has no size or isn't visible.** It needs `addAndMakeVisible(browser)` and bounds in `resized()`.

## The page shows, but the knobs are frozen

1. **A name or type mismatch.** The console says "Creating SliderState for 'x', which is unknown to the backend" (or ToggleState, ComboBoxState). The relay's name and the page's string differ (case counts), or a toggle relay is read with `getSliderState`, or the relay was never passed to `withOptionsFrom`. Run the binding checker.
2. **The library never loaded.** The script isn't `type="module"`, the import path doesn't match a URL the provider serves, or the provider serves the library with a non-JavaScript MIME type. The console shows the failed load or a syntax error at `export`.
3. **State functions called through `window.__JUCE__`.** They aren't there; import them from the library.
4. **Native integration is off.** Without `withNativeIntegrationEnabled()`, the page's messages have no handler. The console shows errors from the library's calls.
5. **No attachment** for the relay, or an attachment to a different parameter than the one you're watching.
6. **The control only listens to DOM events and never calls `setNormalisedValue` / `setValue` / `setChoiceIndex`.**

## The knobs move, but don't follow automation or preset loads

1. **The listener expects an argument.** `valueChangedEvent` calls listeners with none; `(v) => draw(v)` draws `undefined`. Read the value from the state inside the listener.
2. **The page rendered once at start-up** and never listens, or renders before the initial update arrived.
3. **The page skips updates while "dragging"** but never ends the drag (a missing `sliderDragEnded` on pointer-up outside the control or on blur).

## The sound changes, but the host doesn't record automation

1. **No gesture around slider edits.** Call `sliderDragStarted()` before the first `setNormalisedValue` of an edit and `sliderDragEnded()` after the last, on every input path (drag, wheel, keys, reset). Toggles and combo boxes need no calls: their attachments wrap each change in a complete gesture.
2. **The page writes the parameter some other way** (a native function that calls `setValueNotifyingHost` without `beginChangeGesture` / `endChangeGesture`). Go through the relay and attachment instead.
3. The parameter isn't automatable. That's a parameter-design question: see `audio-parameters`.

## The control jumps or lands on wrong values

- The parameter's range uses custom conversion functions or a symmetric skew. The page normalises with only start, end, skew and interval, so its values differ from the host's.
- A combo box attached to a parameter that isn't an `AudioParameterChoice` gets no `choices`, so its index is meaningless.
- The page normalises with its own formula instead of calling `getNormalisedValue()` / `setNormalisedValue()`.

## Crash when the editor closes or reopens

- **Member order.** A relay declared after the browser is destroyed before it, and the browser's destructor then notifies a destroyed relay. An attachment declared before its relay outlives it. Declare relays, then the browser, then the attachments.
- The processor kept a pointer to the editor (see `audio-juce`).

## Console warnings worth knowing

- "which is unknown to the backend": a state or native function name the C++ side doesn't know.
- "The backend expected a @juce-framework/webview version of ...": the page's library and the C++ side come from different JUCE versions. Take the library from the same checkout.
- "The 'window.__JUCE__' object is undefined": the page runs outside the plugin's browser (a normal browser), so nothing will connect.

## JUCE 9.0.6 facts that older advice gets wrong

Advice written for JUCE 8, including some widely copied troubleshooting notes, doesn't hold in 9.0.6. These are the 9.0.6 facts:

- **The Web attachments take two arguments,** the parameter and the relay. The undo manager is an optional third argument that defaults to `nullptr`; whether you pass it has no effect on binding.
- **The interop library is a single file,** `dist/index.js`, with its native-interop check bundled in. There's no second JUCE file to embed or serve.
- **`NEEDS_WEB_BROWSER` only links WebKit on Linux.** On macOS it has no effect on any format. A VST3 missing from a host is an install, cache or plugin-code problem (`audio-juce`).
- **There's no message format to agree on** between the page and the C++ side. Relays, attachments and the library's state functions carry the protocol, on event ids JUCE reserves. Bind controls through them.
- **Plain members, declared relays, browser, attachments, are correct.** `std::unique_ptr` members are optional and change nothing about the order.
- **A `file:` URL loads.** By default only that one file is readable; its siblings are blocked unless `withAllowAccessToEnclosingDirectory(true)`. Serve the page through the resource provider instead.
- **Listen for C++ events on `window.__JUCE__.backend.addEventListener`.** The library exports no `addEventListener`.
- **A choice parameter pairs with `WebComboBoxRelay` and `getComboBoxState`, a bool with `WebToggleButtonRelay` and `getToggleState`.** Each page function finds only relays of its own class.
- **A slider state reads and writes with `getNormalisedValue()`, `getScaledValue()` and `setNormalisedValue()`.** `getValue()` and `setValue()` belong to the toggle state.

## Sources

- JUCE 9.0.6 `modules/juce_audio_processors/utilities/juce_ParameterAttachments.h`: the Web attachments' constructors, undo manager defaulting to `nullptr`.
- JUCE 9.0.6 `modules/juce_gui_extra/native/typescript/webview-interop/`: `dist/` holds one JavaScript file, `index.js`; `src/index.ts` imports the native-interop check into it, defines the state classes and their methods, and logs the warnings quoted above; `src/check_native_interop.ts` defines `window.__JUCE__.backend.addEventListener` and the undefined-object warning.
- JUCE 9.0.6 `docs/CMake API.md`: `NEEDS_WEB_BROWSER` acts on Linux only.
- JUCE 9.0.6 `modules/juce_gui_extra/misc/juce_WebBrowserComponent.h`: reserved `__juce` event ids, `withAllowAccessToEnclosingDirectory`.
- JUCE 9.0.6 `modules/juce_gui_extra/native/juce_WebBrowserComponent_mac.mm`: `file:` URLs and their read access, the message handler, developer extras in debug builds.
- JUCE 9.0.6 `examples/Plugins/WebViewPluginDemo.h`: plain members in the order relays, browser, attachments.
- The older advice this section corrects comes from the Plugin Freedom System's JUCE 8 troubleshooting notes.
