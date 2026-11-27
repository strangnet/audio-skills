# Native integration, native functions, events and navigation

Facts checked against JUCE 9.0.6 on macOS; see Sources. Which thread calls what in the processor belongs to the `audio-juce` skill, and the real-time rules for the audio thread to `audio-dsp`.

## Native integration only for the plugin's own page

- `Options::withNativeIntegrationEnabled()` injects `window.__JUCE__.backend` into every page the browser loads, and with it the power to send events to the C++ side and call its native functions. JUCE's documentation says to enable it only when you fully control what the browser loads.
- Relays need it on (see [relays-and-attachments.md](relays-and-attachments.md)). `withNativeFunction` turns it on by itself.
- **Keep navigation on the plugin's page.** `WebBrowserComponent::pageAboutToLoad` allows every navigation by default, so a link, a form or a script can take the browser, with native integration still on, anywhere. Subclass the browser and allow only the plugin's own page:

  ```cpp
  struct SinglePageBrowser final : juce::WebBrowserComponent
  {
      using WebBrowserComponent::WebBrowserComponent;
      bool pageAboutToLoad (const juce::String& url) override
      {
          return url == getResourceProviderRoot();
      }
  };
  ```

  `pageAboutToLoad` sees navigations, not the page's own script, style and image requests, which go to the resource provider. During development, also allow the dev server's address if you use one, and remove it for release.
- A link that asks for a new window calls `newWindowAttemptingToLoad`, which by default does nothing. To open an external link, override it and hand the URL to the system browser (`juce::URL (url).launchInDefaultBrowser()`), never load it into the plugin's browser.
- Don't let the page load remote scripts or styles (a CDN). The plugin must work offline, and remote code would run with native integration on.

## Native functions: page calls C++

```cpp
.withNativeFunction ("loadPreset", [this] (const juce::Array<juce::var>& args,
                                           juce::WebBrowserComponent::NativeFunctionCompletion complete)
                     {
                         complete (loadPreset (args[0].toString()));
                     })
```

```js
const loadPreset = Juce.getNativeFunction("loadPreset");
const ok = await loadPreset("Warm");
```

- The C++ callback **always runs on the message thread**. It must not block, and it must never call into the audio callback; it changes parameters or hands work to the processor the way any editor code does (`audio-juce`).
- The page's call returns a `Promise` that resolves with the value passed to `complete`. `complete` may be called later and from any thread (JUCE posts it back to the message thread), but it must be called exactly once, or the promise never resolves.
- The name must match on both sides. `getNativeFunction` with a name the C++ side didn't register logs a console warning containing "unknown to the backend", and calling it trips an assertion in a debug build. The binding checker doesn't check native function names.
- Registering the same name twice trips an assertion.

## Events

**Page to C++:** register `Options::withEventListener (eventId, [this] (juce::var payload) { ... })`, and send from the page with `window.__JUCE__.backend.emitEvent(eventId, payload)`. On macOS the listener runs on the message thread (JUCE calls it from WebKit's script-message handler, which runs on the main thread).

**C++ to page:** call `browser.emitEventIfBrowserIsVisible (eventId, payload)` on the message thread, and listen on the page with `window.__JUCE__.backend.addEventListener(eventId, fn)`, which returns a handle for `removeEventListener`. The library doesn't export an `addEventListener`; the backend object is the only place to listen.

- **Send events only after the first page load.** The call needs JUCE's script in the page. Before the page has loaded, it fails: a JavaScript exception in a debug build and an assertion on the C++ side. Override `pageFinishedLoading` to note the first load, and emit nothing before it.
- As the name says, nothing is sent while the browser isn't visible. A page that needs the current state when it shows again asks for it (a native function works well).
- Event ids starting with `__juce` are reserved for JUCE. The relays' traffic uses them; never emit or listen to those ids by hand. A control bound to a parameter goes through a relay and the library's state functions, with no message format of your own.
- The payload is a `juce::var`, sent as JSON. For larger or frequent data, JUCE's demo emits a small event and lets the page fetch the data from the resource provider (`getBackendResourceAddress("data.json")` builds the URL).

## Feeding meters and other audio data

The audio thread never touches the browser. It writes atomics or a lock-free FIFO; a `juce::Timer` on the editor reads them on the message thread and emits an event or answers a fetch. Real-time rules for the writing side: `audio-dsp`. Parameter listeners can run on the audio thread, so they don't emit either.

## Seeing the page's console

In a debug build on macOS JUCE turns on WebKit's developer extras: right-click the page and choose Inspect Element to open Web Inspector. That console is where "unknown to the backend", a failed module load, a MIME-type refusal and the library-version warning show up. JUCE doesn't turn it on in release builds.

## Sources

- JUCE 9.0.6 `modules/juce_gui_extra/misc/juce_WebBrowserComponent.h`: `withNativeIntegrationEnabled` (and its security note), `withNativeFunction` (message thread), `NativeFunctionCompletion` (any thread), `withEventListener`, `emitEventIfBrowserIsVisible` (reserved `__juce` ids, only after the first page load), `pageAboutToLoad`, `pageFinishedLoading`, `newWindowAttemptingToLoad`.
- JUCE 9.0.6 `modules/juce_gui_extra/misc/juce_WebBrowserComponent.cpp`: native functions turn native integration on; duplicate and unknown function names assert; completions from other threads are posted to the message thread; `pageAboutToLoad` returns `true` and `newWindowAttemptingToLoad` does nothing by default; events emitted only while visible.
- JUCE 9.0.6 `modules/juce_gui_extra/native/juce_WebBrowserComponent_mac.mm`: navigation policy calls `pageAboutToLoad`, new-window requests call `newWindowAttemptingToLoad`, script messages delivered to the event listeners, developer extras enabled in debug builds.
- JUCE 9.0.6 `modules/juce_gui_extra/native/typescript/webview-interop/src/index.ts` and `src/check_native_interop.ts`: `getNativeFunction` (promise, "unknown to the backend" warning), `getBackendResourceAddress`, `window.__JUCE__.backend` with `addEventListener`, `removeEventListener` and `emitEvent`.
- JUCE 9.0.6 `modules/juce_core/network/juce_URL.h`: `launchInDefaultBrowser`.
- JUCE 9.0.6 `examples/Plugins/WebViewPluginDemo.h`: `SinglePageBrowser`, a timer that emits a small event, data served through the provider.
