# Serving the page and the interop library

Facts checked against JUCE 9.0.6 on macOS; see Sources. JUCE material is paraphrased. CMake setup of the plugin itself (formats, codes, finding JUCE) belongs to the `audio-juce` skill.

## The browser needs nothing from CMake on macOS

- `WebBrowserComponent` lives in `juce_gui_extra`, which `juce_audio_processors` depends on, so linking `juce::juce_audio_utils` (or `juce_audio_processors`) is enough. The relays and the Web attachments come with `<juce_audio_processors/juce_audio_processors.h>`.
- `JUCE_WEB_BROWSER` defaults to `1`. Don't set it to `0` (JUCE's CMake plugin example does, to save code size).
- `NEEDS_WEB_BROWSER` only links WebKit on Linux. On macOS it changes nothing, so it is never the reason a format is missing from a host. A format that is missing or stale in a host is a bundle or cache problem: see `audio-juce`.

## Serve the page through the resource provider

- Register a provider with `Options::withResourceProvider(provider)` and open the page with `browser.goToURL(juce::WebBrowserComponent::getResourceProviderRoot())`. Never hard-code the root (on macOS it's `juce://juce.backend/`); the call returns the right one for the platform.
- **The root arrives as `/`.** A request for root + `path` reaches the provider as `/path`. Map `/` to your `index.html`, and strip the leading slash for everything else. A provider that only knows `/index.html` returns nothing for the first request, and the page stays blank.
- The provider returns `std::optional<WebBrowserComponent::Resource>`: the bytes (`std::vector<std::byte>`) and a MIME type. Returning `std::nullopt` makes the web view answer 404.
- The path the provider receives has no query string: JUCE's macOS scheme handler passes only the URL's path.
- The page and all its files come from inside the plugin binary, so the plugin needs no files installed beside it and no network.

### Why not a file URL

`goToURL` with a `file:` URL does load on macOS, but:
- the files must be installed at a path the plugin knows at run time, for every user and every host;
- by default the web view may read only the file it was pointed at. The page's sibling files (its scripts, styles, JUCE's library) are blocked unless `Options::AppleWkWebView::withAllowAccessToEnclosingDirectory(true)` is set, which JUCE marks as a security risk when you don't control the folder's contents.

Use the resource provider instead.

## Map each URL to its embedded file, with the right MIME type

- `juce_add_binary_data(<Target> NAMESPACE <Ns> HEADER_NAME <Header>.h SOURCES ...)` embeds files as `<Ns>::<identifier>` and `<Ns>::<identifier>Size`. The identifier comes from the **file name only**: folders are dropped, and dots and spaces become underscores (`ui/js/juce/index.js` becomes `index_js`). A second file with the same name gets a numeric suffix (`index_js2`). So the page's URLs and the embedded names can't be matched by a generic loop over `namedResourceList`.
- Write an explicit table: URL path, embedded data and size, MIME type. The tilt-EQ example and JUCE's own demo both do this:

  ```cpp
  struct Entry { const char* path; const char* data; int size; const char* mime; };
  static const Entry files[] = {
      { "index.html",   Ui::index_html, Ui::index_htmlSize, "text/html" },
      { "juce/index.js", Ui::index_js,  Ui::index_jsSize,   "text/javascript" },
  };
  const auto path = url == "/" ? juce::String ("index.html")
                               : url.fromFirstOccurrenceOf ("/", false, false);
  ```
- **MIME types matter.** JUCE sends the type you return as the response's `Content-Type`. A browser runs a module script only when it's served with a JavaScript MIME type (`text/javascript`), so a script served as `text/plain`, `application/octet-stream` or an empty string fails to load, and every control on the page stays frozen. Use `text/html`, `text/javascript`, `text/css`, `application/json`, `image/svg+xml`, `image/png`, `font/woff2` and so on. JUCE's demo maps extensions to types and asserts on an unknown one.
- **Serve every file the page references**, including files a bundler emits (chunks, source maps, fonts). The binding checker can't see whether the provider serves them.
- A page built by a bundler can also be embedded as a zip and read with `juce::ZipFile`, as JUCE's demo does. The same rules apply: the root is `/`, and each entry needs its MIME type.

## JUCE's interop library

The page reaches the relays through JUCE's JavaScript library. Take it from the same JUCE version as the C++ side:
- **From the JUCE checkout:** `modules/juce_gui_extra/native/typescript/webview-interop/dist/index.js`. Embed it straight from `${JUCE_DIR}` in `juce_add_binary_data` (the tilt-EQ example does), so it can't drift from the C++.
- **From npm:** `@juce-framework/webview`, at the version in that folder's `package.json` (it's `1.0.0` in JUCE 9.0.6; the package doesn't share JUCE's version number). A bundled page can also depend on the checkout itself with a `file:` dependency, as JUCE's demo does.

JUCE 9 checks the match at run time. CMake reads the library version from the checkout's `package.json` into the C++ build; when native integration is on, the page reports its own version on load. A mismatch logs a console warning in the page and trips an assertion in a debug build.

**One file.** JUCE 9's built `index.js` bundles its native-interop check, so the page loads that single file and nothing else from JUCE. (JUCE 8's library imported a second file, `check_native_interop.js`, that also had to be served. In 9.0.6 there's no such file in `dist/` and nothing to serve.)

### Load it as an ES module and import from it

The library is an ES module: it `export`s `getSliderState`, `getToggleState`, `getComboBoxState`, `getNativeFunction`, `getBackendResourceAddress` and `ControlParameterIndexUpdater`, and nothing else.

```html
<script type="module">
  import * as Juce from "./juce/index.js";
  const drive = Juce.getSliderState("drive");
</script>
```

- Every script that imports from it needs `type="module"`. A classic `<script src=".../index.js">` throws on the `export` and defines nothing.
- The state functions are **not** on `window.__JUCE__`. That object only carries JUCE's low-level plumbing (`backend`, `initialisationData`, `postMessage`). Call the functions you imported.
- `window.__JUCE__.backend.addEventListener(eventId, fn)` is the right way to listen for events the C++ side emits; see [native-functions-events-and-navigation.md](native-functions-events-and-navigation.md).
- The import path is relative to the page and must match a URL the provider serves (`./juce/index.js` above maps to `juce/index.js` in the table).
- A page that runs outside a plugin (in a normal browser while you design it) still loads: the library logs a warning and installs placeholders, but no events arrive and nothing is saved.

## A development server

`withResourceProvider(provider, allowedOrigin)` lets a page loaded from a local development server (`http://localhost:3000`, say) fetch from the provider, and JUCE's demo can `goToURL` that server during development. JUCE flags the allowed origin as a security risk in released builds: ship with the page embedded and no allowed origin.

## When the editor is hidden

By default JUCE replaces the page with a blank one while the browser isn't visible, to save resources, and loads it again when it shows. `Options::withKeepPageLoadedWhenBrowserIsHidden()` keeps it loaded. Either way, and because the host destroys the whole editor when its window closes (see `audio-juce`), the page must rebuild its display from the states' initial updates, never from JavaScript variables it assumes survived.

## Sources

- JUCE 9.0.6 `modules/juce_gui_extra/misc/juce_WebBrowserComponent.h`: `withResourceProvider` (the `/` root, `/path` requests, the allowed origin and its risk), `getResourceProviderRoot`, `AppleWkWebView::withAllowAccessToEnclosingDirectory` (off by default, security note), `withKeepPageLoadedWhenBrowserIsHidden`.
- JUCE 9.0.6 `modules/juce_gui_extra/native/juce_WebBrowserComponent_mac.mm`: the `juce` URL scheme handler (path only, `Content-Type` from the resource, 404 for no resource), `file:` URLs loaded with read access to the file or its folder.
- JUCE 9.0.6 `modules/juce_gui_extra/misc/juce_WebBrowserComponent.cpp`: the per-platform root, the version-check native function and its assertion.
- JUCE 9.0.6 `extras/Build/CMake/JUCEModuleSupport.cmake`: `JUCE_WEBVIEW_INTEROP_LIBRARY_VERSION` read from the interop library's `package.json`.
- JUCE 9.0.6 `modules/juce_gui_extra/native/typescript/webview-interop/`: `package.json` (name `@juce-framework/webview`, version `1.0.0`, `dist/index.js` as the module entry), `README.md` (matching versions, browser mocks), `src/index.ts` (export list, the version warning, the bundled `check_native_interop` import), `build.mjs` (one bundled ES module).
- JUCE 9.0.6 `modules/juce_gui_extra/juce_gui_extra.h` (`JUCE_WEB_BROWSER` defaults to 1), `modules/juce_audio_processors/juce_audio_processors.h` (depends on `juce_gui_extra`), `docs/CMake API.md` (`NEEDS_WEB_BROWSER` is Linux-only, `juce_add_binary_data`).
- JUCE 9.0.6 `extras/Build/juce_build_tools/utils/juce_BuildHelperFunctions.cpp` and `juce_BinaryResourceFile.cpp`: binary-data identifiers from the file name, with numeric suffixes for duplicates.
- JUCE 9.0.6 `examples/Plugins/WebViewPluginDemo.h` and `WebViewPluginDemoGUI/package.json`: the explicit MIME map, the zip, the dev-server origin, the `file:` dependency on the checkout.
- The module-script MIME rule is the web platform's (HTML Standard, module scripts), not JUCE's.
