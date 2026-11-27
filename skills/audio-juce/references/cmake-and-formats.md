# CMake and formats

Facts checked against JUCE 9.0.6 and clap-juce-extensions at commit `3837f4a6ed2ab0ba46aba69ae5b7041c7c64ce74`. JUCE material is paraphrased; see Sources.

## Finding JUCE

JUCE 9 needs CMake 3.22 or later and C++17 or later. It joins a project in one of two ways:

- `add_subdirectory(<JUCE checkout> <binary dir>)`, which also defines the `juce_add_*` functions.
- `find_package(JUCE CONFIG REQUIRED)` after installing JUCE with its own install target, with the install prefix passed through `CMAKE_PREFIX_PATH`.

Either way, the location comes from outside the project: a cache variable that defaults to an environment variable, so a developer can set it once in their shell or pass `-DJUCE_DIR=...` on the command line.

```cmake
set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH "Path to a JUCE 9.0.x checkout")
if(NOT EXISTS "${JUCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "Set JUCE_DIR (cache variable or environment) to a JUCE 9.0.x checkout")
endif()
add_subdirectory("${JUCE_DIR}" juce)
```

A hard-coded `/Users/<name>/JUCE` works on one machine only. A git submodule at a relative path is also fine.

## `juce_add_plugin`: the options that matter

| Option | What to set | Why |
|---|---|---|
| `PLUGIN_CODE` | Four characters, fixed and unique per plugin, exactly one upper-case letter (`Tilt`) | Left out, JUCE generates a random code that changes each time the build is configured. AU needs exactly one upper-case letter; GarageBand 10.3 wants the first letter upper-case and the rest lower-case. |
| `PLUGIN_MANUFACTURER_CODE` | Four characters, fixed, yours, at least one upper-case letter (`Stng`) | Defaults to `Manu`, shared with every project that forgot it. AU needs at least one upper-case letter. |
| `COMPANY_NAME`, `BUNDLE_ID` | Your company and a reverse-DNS id | `BUNDLE_ID` is otherwise generated from `COMPANY_NAME` and the CMake target's name, so renaming either changes it. |
| `PRODUCT_NAME` | The bundle's file name | Renaming it later leaves the old bundles installed. |
| `PLUGIN_NAME` | The name hosts display | Defaults to `PRODUCT_NAME`. |
| `FORMATS` | `VST3 AU` | Valid values in 9.0.6: `Standalone Unity VST3 AU AUv3 AAX VST LV2`. No CLAP. AU builds only on macOS. |
| `IS_SYNTH`, `NEEDS_MIDI_INPUT`, `NEEDS_MIDI_OUTPUT`, `IS_MIDI_EFFECT` | Per plugin type | See [buses-and-plugin-types.md](buses-and-plugin-types.md). All default to `FALSE`. |
| `VST3_CATEGORIES`, `AU_MAIN_TYPE` | Usually leave unset | JUCE derives them from `IS_SYNTH`, `IS_MIDI_EFFECT` and `NEEDS_MIDI_INPUT`. An explicit value overrides the derived one, including a wrong value copied from a template. |
| `COPY_PLUGIN_AFTER_BUILD` | Your choice | Defaults to `FALSE`. When `TRUE`, the build installs the bundles to the system plug-in folders, which is what hosts scan. |

## Headers

Include each module's header directly, for example `<juce_audio_processors/juce_audio_processors.h>` and `<juce_audio_utils/juce_audio_utils.h>`. In 9.0.6 `AudioProcessor` itself lives in the `juce_audio_processors_headless` module, which `juce_audio_processors` includes and depends on. `JuceHeader.h` is optional in a plain CMake project: it exists only if you call `juce_generate_juce_header(<target>)`, and it adds a `using namespace juce` unless told not to. An `#include <JuceHeader.h>` copied from a Projucer project fails with "file not found" in a CMake project that never generated it.

Link `juce::juce_audio_utils` (it pulls in the processor modules), and optionally `juce::juce_recommended_config_flags`, `juce::juce_recommended_lto_flags` and `juce::juce_recommended_warning_flags`, as JUCE's own plugin example does.

## Compile definitions worth deciding on day one

- `JUCE_VST3_CAN_REPLACE_VST2` defaults to `1`, which makes the VST3 load and save VST2-compatible state. Set it to `0` in a new plugin with no VST2 history, as JUCE's CMake plugin example does. Changing it after release makes the VST3 incompatible with its earlier versions.
- `JUCE_WEB_BROWSER` defaults to `1`. JUCE's plugin example sets it to `0` to save code size; a WebView editor needs it left on.
- `NEEDS_WEB_BROWSER` and `NEEDS_CURL` act only on Linux and BSD, where they link WebKit or curl and set the matching definition. On macOS they change nothing.
- `JUCE_USE_CURL=0` is fine for a plugin that makes no network requests.

## CLAP through clap-juce-extensions

JUCE 9.0.6 has no CLAP client: `CLAP` isn't a valid `FORMATS` value. Use [clap-juce-extensions](https://github.com/free-audio/clap-juce-extensions), pinned to a commit you have built and validated, and change the pin only after re-validating. The commit tested with JUCE 9.0.6 for this package is `3837f4a6ed2ab0ba46aba69ae5b7041c7c64ce74`.

- Fetch it after JUCE is added, with its submodules (it carries `clap` and `clap-helpers` as submodules), and add it with `EXCLUDE_FROM_ALL`. With `FetchContent`: `GIT_TAG <commit>` and `GIT_SUBMODULES_RECURSE TRUE`.
- After `juce_add_plugin`, call `clap_juce_extensions_plugin(TARGET <target> CLAP_ID "<reverse-dns id>" CLAP_FEATURES <features>)`. It creates a `<target>_CLAP` target.
- `CLAP_ID` is required (configure fails without it) and is the CLAP's identity: fix it like the plugin code.
- `CLAP_FEATURES` defaults to `instrument` with only a warning. Always pass it: `audio-effect` (plus, say, `equalizer stereo mono`) for an effect, `instrument synthesizer` for a synth, `note-effect` for a MIDI effect.
- In the CLAP build, `wrapperType` is `wrapperType_Undefined`, so code that branches on the wrapper type can't tell CLAP apart that way.
- CLAP parameter ids are hashed from the JUCE parameter ids, the same way JUCE's VST3 wrapper does it, and state goes through `getStateInformation` and `setStateInformation` unchanged. Stable JUCE ids give stable CLAP ids.

```cmake
include(FetchContent)
FetchContent_Declare(clap-juce-extensions
    GIT_REPOSITORY https://github.com/free-audio/clap-juce-extensions.git
    GIT_TAG 3837f4a6ed2ab0ba46aba69ae5b7041c7c64ce74
    GIT_SUBMODULES_RECURSE TRUE)
FetchContent_GetProperties(clap-juce-extensions)
if(NOT clap-juce-extensions_POPULATED)
    FetchContent_Populate(clap-juce-extensions)
    add_subdirectory(${clap-juce-extensions_SOURCE_DIR} ${clap-juce-extensions_BINARY_DIR} EXCLUDE_FROM_ALL)
endif()

# after juce_add_plugin(MyEq ...)
clap_juce_extensions_plugin(TARGET MyEq
    CLAP_ID "com.example.myeq"
    CLAP_FEATURES audio-effect equalizer stereo)
```

## Sources

- JUCE 9.0.6 `docs/CMake API.md`: system requirements, `add_subdirectory` and `find_package`, the `BUNDLE_ID`, `FORMATS`, `PLUGIN_NAME`, `PLUGIN_MANUFACTURER_CODE`, `PLUGIN_CODE`, `IS_SYNTH`, `NEEDS_MIDI_INPUT`, `VST3_CATEGORIES`, `AU_MAIN_TYPE`, `NEEDS_WEB_BROWSER` and `COPY_PLUGIN_AFTER_BUILD` options, and `juce_generate_juce_header`.
- JUCE 9.0.6 `extras/Build/CMake/JUCEUtils.cmake`: the plugin defaults (`Manu`, the random plugin code, the derived `VST3_CATEGORIES` and `AU_MAIN_TYPE`), `_juce_link_optional_libraries` (Linux and BSD only), and the C++17 compile feature.
- JUCE 9.0.6 `examples/CMake/AudioPlugin/CMakeLists.txt`: the compile definitions and recommended flag targets.
- JUCE 9.0.6 `modules/juce_audio_plugin_client/juce_audio_plugin_client.h` (`JUCE_VST3_CAN_REPLACE_VST2`), `modules/juce_gui_extra/juce_gui_extra.h` (`JUCE_WEB_BROWSER`), `modules/juce_audio_processors/juce_audio_processors.h` (its dependency on `juce_audio_processors_headless`).
- clap-juce-extensions at commit `3837f4a6ed2ab0ba46aba69ae5b7041c7c64ce74`: `README.md` (setup, submodules, `wrapperType`, parameter ids and state), `cmake/ClapTargetHelpers.cmake` (`CLAP_ID` required, `CLAP_FEATURES` default), `clap-libs/clap/include/clap/plugin-features.h` (feature names).
- This package's tilt-EQ example (`examples/tilt-eq/juce/CMakeLists.txt` in the strangnet-audio-skills repo) builds VST3, AU and CLAP this way and passes pluginval, auval and clap-validator.
