"""WebView binding check: the relays an editor's C++ creates and the states its
page requests must name each other."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "audio-juce-webview" / "scripts" / "check_webview_bindings.py"
EXAMPLE_JUCE = REPO / "examples" / "tilt-eq" / "juce"


def write(path, text=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run_check(*paths):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)], capture_output=True, text=True
    )


# Zero


def test_editor_with_no_relays_and_no_states_passes(tmp_path):
    # Given an editor source with no relays and a page with no state requests
    write(tmp_path / "Source" / "PluginEditor.cpp", "void Editor::resized() {}\n")
    write(tmp_path / "ui" / "index.html", "<html><body>Hello</body></html>\n")

    # When the binding check runs on both folders
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then it reports nothing and exits with success
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


# One


def test_relay_and_state_with_the_same_name_pass(tmp_path):
    # Given a "gain" slider relay and a page that requests the "gain" slider state
    write(
        tmp_path / "Source" / "PluginEditor.h",
        "struct Editor {\n    juce::WebSliderRelay gainRelay{\"gain\"};\n};\n",
    )
    write(
        tmp_path / "ui" / "main.js",
        'import { getSliderState } from "./juce/index.js";\nconst gain = getSliderState("gain");\n',
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then it reports nothing and exits with success
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_relay_with_no_matching_state_is_a_relay_name_error(tmp_path):
    # Given an editor with a "gain" slider relay and a page that requests no state
    editor = tmp_path / "Source" / "PluginEditor.h"
    write(editor, "struct Editor {\n    juce::WebSliderRelay gainRelay{\"gain\"};\n};\n")
    write(tmp_path / "ui" / "index.html", "<html><body></body></html>\n")

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then the relay is reported where it is created, and the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f'{editor}:2: error: relay-name: relay "gain" has no matching state in the page'
    ]


def test_state_with_no_matching_relay_is_a_relay_name_error(tmp_path):
    # Given an editor with no relays and a page that requests the "gain" slider state
    write(tmp_path / "Source" / "PluginEditor.cpp", "void Editor::resized() {}\n")
    page = tmp_path / "ui" / "main.js"
    write(page, 'import { getSliderState } from "./juce/index.js";\nconst gain = getSliderState("gain");\n')

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then the state is reported where it is requested, and the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f'{page}:2: error: relay-name: state "gain" has no matching relay in the C++'
    ]


def test_relay_requested_with_the_wrong_state_function_is_a_relay_type_error(tmp_path):
    # Given a "gain" slider relay and a page that reads "gain" with the toggle state
    write(
        tmp_path / "Source" / "PluginEditor.h",
        "struct Editor {\n    juce::WebSliderRelay gainRelay{\"gain\"};\n};\n",
    )
    page = tmp_path / "ui" / "main.js"
    write(page, 'import { getToggleState } from "./juce/index.js";\nconst gain = getToggleState("gain");\n')

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then the request is reported as the wrong type, not as an unmatched name, and
    # the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f'{page}:2: error: relay-type: state "gain" is requested with getToggleState,'
        " but its relay is a WebSliderRelay (use getSliderState)"
    ]


def test_computed_relay_names_in_the_cpp_are_one_warning(tmp_path):
    # Given slider relays built in a loop from a parameter table, and a page that
    # requests two slider states by literal name
    editor = tmp_path / "Source" / "PluginEditor.cpp"
    write(
        editor,
        "Editor::Editor() {\n"
        "    for (auto& p : core::parameters)\n"
        "        relays.push_back (std::make_unique<juce::WebSliderRelay> (p.id));\n"
        "}\n",
    )
    write(tmp_path / "ui" / "main.js", 'getSliderState("tilt");\ngetSliderState("level");\n')

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then one warning says the slider names can't be matched, the page's slider
    # states aren't reported, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{editor}:3: warning: relay-name: WebSliderRelay names are computed in the C++,"
        " so getSliderState names can't be matched"
    ]


def test_computed_state_names_in_the_page_are_one_warning(tmp_path):
    # Given two literal slider relays, and a page that requests slider states in a
    # loop over a list of ids
    write(
        tmp_path / "Source" / "PluginEditor.h",
        'juce::WebSliderRelay tilt{"tilt"};\njuce::WebSliderRelay level{"level"};\n',
    )
    page = tmp_path / "ui" / "main.js"
    write(
        page,
        'import * as Juce from "./juce/index.js";\n'
        'for (const id of ["tilt", "level"]) {\n'
        "    const state = Juce.getSliderState(id);\n"
        "}\n",
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then one warning says the slider names can't be matched, the relays aren't
    # reported, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{page}:3: warning: relay-name: getSliderState names are computed in the page,"
        " so WebSliderRelay names can't be matched"
    ]


# Many


def test_every_relay_construction_form_is_found(tmp_path):
    # Given relays of all three classes, created in a brace or parenthesis declaration
    # or through make_unique, and a page that requests each one with its state function
    write(
        tmp_path / "Source" / "PluginEditor.h",
        "struct Editor {\n"
        '    juce::WebSliderRelay cutoff { "cutoff" };\n'
        '    WebToggleButtonRelay bypass ("bypass");\n'
        "    std::unique_ptr<juce::WebSliderRelay> drive, mix;\n"
        "    std::unique_ptr<juce::WebComboBoxRelay> mode;\n"
        "};\n",
    )
    write(
        tmp_path / "Source" / "PluginEditor.cpp",
        'Editor::Editor() {\n    drive = std::make_unique<juce::WebSliderRelay> ("drive");\n'
        '    mix = make_unique<WebSliderRelay>("mix");\n'
        '    mode = std::make_unique<juce::WebComboBoxRelay>("mode");\n}\n',
    )
    write(
        tmp_path / "ui" / "main.js",
        'import { getSliderState, getToggleState, getComboBoxState } from "./juce/index.js";\n'
        'getSliderState("cutoff"); getSliderState("drive"); getSliderState("mix");\n'
        'getToggleState("bypass"); getComboBoxState("mode");\n',
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then every relay matches its state and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_every_state_request_form_is_found(tmp_path):
    # Given four slider relays, and a page that requests them through a namespace
    # import, a renamed import, an inline script in HTML and a .mjs module
    write(
        tmp_path / "Source" / "PluginEditor.h",
        "struct Editor {\n"
        '    juce::WebSliderRelay a{"a"}, b{"b"}, c{"c"}, d{"d"};\n'
        "};\n",
    )
    write(
        tmp_path / "ui" / "index.html",
        "<html><body>\n<script type=\"module\">\n"
        "  import * as Juce from './juce/index.js';\n"
        "  Juce.getSliderState('a');\n"
        "</script>\n</body></html>\n",
    )
    write(
        tmp_path / "ui" / "controls.js",
        'import { getSliderState as slider } from "./juce/index.js";\nslider("b");\n',
    )
    write(
        tmp_path / "ui" / "more.mjs",
        'import { getSliderState } from "./juce/index.js";\ngetSliderState(\n  "c");\n'
        'getSliderState(`d`);\n',
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then every state matches its relay and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_every_wrong_state_function_is_a_relay_type_error(tmp_path):
    # Given one relay of each class, and a page that reads each with another
    # class's state function
    write(
        tmp_path / "Source" / "PluginEditor.h",
        "struct Editor {\n"
        '    juce::WebSliderRelay cutoff{"cutoff"};\n'
        '    juce::WebToggleButtonRelay bypass{"bypass"};\n'
        '    juce::WebComboBoxRelay mode{"mode"};\n'
        "};\n",
    )
    page = tmp_path / "ui" / "main.js"
    write(
        page,
        'import * as Juce from "./juce/index.js";\n'
        'Juce.getToggleState("cutoff");\n'
        'Juce.getComboBoxState("bypass");\n'
        'Juce.getSliderState("mode");\n',
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then each request is reported as the wrong type, and the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f'{page}:2: error: relay-type: state "cutoff" is requested with getToggleState,'
        " but its relay is a WebSliderRelay (use getSliderState)",
        f'{page}:3: error: relay-type: state "bypass" is requested with getComboBoxState,'
        " but its relay is a WebToggleButtonRelay (use getToggleState)",
        f'{page}:4: error: relay-type: state "mode" is requested with getSliderState,'
        " but its relay is a WebComboBoxRelay (use getComboBoxState)",
    ]


def test_computed_names_give_one_warning_per_relay_type_and_spare_other_types(tmp_path):
    # Given literal relays of all three classes, and a page that computes slider
    # names at two sites and toggle names at one, requests a slider state no relay
    # has, and requests a combo box state whose name no relay has
    editor = tmp_path / "Source" / "PluginEditor.h"
    write(
        editor,
        "struct Editor {\n"
        '    juce::WebSliderRelay cutoff{"cutoff"}, drive{"drive"};\n'
        '    juce::WebToggleButtonRelay bypass{"bypass"};\n'
        '    juce::WebComboBoxRelay mode{"mode"};\n'
        "};\n",
    )
    page = tmp_path / "ui" / "main.js"
    write(
        page,
        'import * as Juce from "./juce/index.js";\n'
        'const sliders = ["cutoff", "drive"].map((id) => Juce.getSliderState(id));\n'
        "const extra = Juce.getSliderState(name);\n"
        "const toggle = Juce.getToggleState(toggleId);\n"
        'Juce.getSliderState("orphan");\n'
        'Juce.getComboBoxState("mood");\n',
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then each computed type gives one warning at its first site, their unmatched
    # names aren't reported, the combo box names still are, and the check fails
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{page}:2: warning: relay-name: getSliderState names are computed in the page,"
        " so WebSliderRelay names can't be matched",
        f"{page}:4: warning: relay-name: getToggleState names are computed in the page,"
        " so WebToggleButtonRelay names can't be matched",
        f'{editor}:4: error: relay-name: relay "mode" has no matching state in the page',
        f'{page}:6: error: relay-name: state "mood" has no matching relay in the C++',
    ]


@pytest.mark.parametrize(
    "construction",
    [
        "juce::WebSliderRelay relay { id };",
        "juce::WebSliderRelay relay (core::ids[0]);",
        "relays[i] = std::make_unique<juce::WebSliderRelay> (ids[i]);",
        "relays.push_back (std::make_unique<WebSliderRelay> (juce::String (p.id)));",
    ],
    ids=["brace variable", "parenthesis table lookup", "make_unique in a loop", "wrapped"],
)
def test_every_computed_relay_form_is_a_warning(tmp_path, construction):
    # Given a slider relay built from something other than a string literal, and a
    # page that requests a slider state whose name no literal relay has
    editor = tmp_path / "Source" / "PluginEditor.cpp"
    write(editor, f"void Editor::make() {{\n    {construction}\n}}\n")
    write(tmp_path / "ui" / "main.js", 'getSliderState("tilt");\n')

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then the construction gives the one warning, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{editor}:2: warning: relay-name: WebSliderRelay names are computed in the C++,"
        " so getSliderState names can't be matched"
    ]


@pytest.mark.parametrize(
    "request_",
    [
        "getSliderState(id);",
        "getSliderState(`${prefix}Gain`);",
        'getSliderState("band" + i);',
        "ids.forEach((id) => getSliderState(id));",
    ],
    ids=["variable", "template with substitution", "concatenation", "loop"],
)
def test_every_computed_state_form_is_a_warning(tmp_path, request_):
    # Given a literal slider relay, and a page that requests a slider state with
    # something other than a string literal
    write(tmp_path / "Source" / "PluginEditor.h", 'juce::WebSliderRelay tilt{"tilt"};\n')
    page = tmp_path / "ui" / "main.js"
    write(page, f'import {{ getSliderState }} from "./juce/index.js";\n{request_}\n')

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then the request gives the one warning, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{page}:2: warning: relay-name: getSliderState names are computed in the page,"
        " so WebSliderRelay names can't be matched"
    ]


def test_typescript_and_jsx_pages_are_read(tmp_path):
    # Given three slider relays, and pages in .ts, .tsx and .jsx that request them,
    # with TypeScript type annotations and assertions around the calls
    write(
        tmp_path / "Source" / "PluginEditor.h",
        'juce::WebSliderRelay a{"a"}, b{"b"}, c{"c"};\n',
    )
    write(
        tmp_path / "ui" / "src" / "state.ts",
        'import * as Juce from "juce-framework-frontend";\n'
        'const a: SliderState = Juce.getSliderState("a") as SliderState;\n',
    )
    write(
        tmp_path / "ui" / "src" / "Knob.tsx",
        'import { getSliderState } from "juce-framework-frontend";\n'
        "export function Knob(): JSX.Element {\n"
        '  const state = getSliderState("b")!;\n'
        "  return <div>{state.getScaledValue()}</div>;\n"
        "}\n",
    )
    write(
        tmp_path / "ui" / "src" / "Fader.jsx",
        'import { getSliderState } from "juce-framework-frontend";\n'
        'export const Fader = () => <input value={getSliderState("c").getScaledValue()} />;\n',
    )

    # When the binding check runs on the editor sources and the source folder
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then every state matches its relay and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


# Boundaries


def test_names_only_in_comments_strings_or_visible_text_are_not_counted(tmp_path):
    # Given one real relay and state, and ghost relays and states that appear only in
    # comments, in strings that aren't state-call arguments, and in the page's text
    write(
        tmp_path / "Source" / "PluginEditor.h",
        "struct Editor {\n"
        '    juce::WebSliderRelay real{"real"};\n'
        '    // juce::WebSliderRelay old{"old"};\n'
        '    /* WebToggleButtonRelay older("older"); */\n'
        '    const char* help = "WebSliderRelay gain{\\"gain\\"}";\n'
        "};\n",
    )
    write(
        tmp_path / "ui" / "main.js",
        'import { getSliderState } from "./juce/index.js";\n'
        'getSliderState("real");\n'
        '// getSliderState("ghost1");\n'
        '/* getSliderState("ghost2"); */\n'
        "console.log('call getSliderState(\"ghost3\")');\n",
    )
    write(
        tmp_path / "ui" / "index.html",
        '<html><body>\n<p>Use getSliderState("ghost4") to read a slider.</p>\n'
        '<!-- getSliderState("ghost5") -->\n<script src="main.js" type="module"></script>\n'
        "</body></html>\n",
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then only the real names are counted, they match, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_dependency_and_build_folders_are_not_read(tmp_path):
    # Given a plugin folder whose own relay and state match, plus orphan relays and
    # states inside node_modules, .git, a _deps folder and a CMake build folder
    plugin = tmp_path / "plugin"
    write(plugin / "Source" / "PluginEditor.h", 'juce::WebSliderRelay gain{"gain"};\n')
    write(plugin / "ui" / "main.js", 'getSliderState("gain");\n')
    write(plugin / "ui" / "node_modules" / "lib" / "index.js", 'getSliderState("npm");\n')
    write(plugin / ".git" / "hooks" / "x.js", 'getSliderState("git");\n')
    write(plugin / "_deps" / "juce-src" / "Demo.h", 'WebSliderRelay demo{"demo"};\n')
    write(plugin / "out" / "CMakeCache.txt", "CMAKE_BUILD_TYPE:STRING=Release\n")
    write(plugin / "out" / "generated" / "Editor.h", 'WebSliderRelay built{"built"};\n')

    # When the binding check runs on the plugin folder
    result = run_check(plugin)

    # Then only the plugin's own files are read, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_relay_class_used_only_as_a_type_is_not_computed(tmp_path):
    # Given relay classes named in pointer members, a container and a parameter,
    # and a member initialised with make_unique of a literal, and a page that
    # requests each literal name
    write(
        tmp_path / "Source" / "PluginEditor.h",
        "struct Editor {\n"
        "    std::unique_ptr<juce::WebSliderRelay> drive, mix;\n"
        "    std::unique_ptr<juce::WebToggleButtonRelay> bypass {\n"
        '        std::make_unique<juce::WebToggleButtonRelay> ("bypass") };\n'
        "    std::vector<std::unique_ptr<juce::WebComboBoxRelay>> combos;\n"
        "    void attach (juce::WebSliderRelay& relay);\n"
        "};\n",
    )
    write(
        tmp_path / "Source" / "PluginEditor.cpp",
        'Editor::Editor() {\n    drive = std::make_unique<juce::WebSliderRelay> ("drive");\n'
        '    mix = std::make_unique<juce::WebSliderRelay> ("mix");\n}\n',
    )
    write(
        tmp_path / "ui" / "main.js",
        'getSliderState("drive"); getSliderState("mix"); getToggleState("bypass");\n',
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then none of the type uses counts as a computed name, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_state_function_definitions_are_not_computed_requests(tmp_path):
    # Given a literal slider relay, a page that requests it, and page code that
    # defines or declares functions named like the state functions
    write(tmp_path / "Source" / "PluginEditor.h", 'juce::WebSliderRelay tilt{"tilt"};\n')
    write(tmp_path / "ui" / "main.js", 'getSliderState("tilt");\n')
    write(
        tmp_path / "ui" / "lib" / "interop.js",
        "function getSliderState(name) {\n  return sliderStates.get(name);\n}\n",
    )
    write(
        tmp_path / "ui" / "types.d.ts",
        "declare function getToggleState(name: string): ToggleState;\n",
    )

    # When the binding check runs
    result = run_check(tmp_path / "Source", tmp_path / "ui")

    # Then the definitions aren't requests, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


# Exceptions


def test_missing_path_is_a_usage_error(tmp_path):
    # Given a path that doesn't exist
    missing = tmp_path / "nowhere"

    # When the binding check runs on it
    result = run_check(missing)

    # Then it prints usage and the path, and exits with the usage-error code
    assert result.returncode == 2, result.stdout + result.stderr
    assert "usage:" in result.stderr
    assert f"no such file or folder: {missing}" in result.stderr


@pytest.mark.parametrize(
    ("present", "message"),
    [
        ({"ui/index.html": "<html></html>\n"},
         "no C++ files (.h, .hpp, .cpp, .cc, .cxx) found"),
        ({"Source/PluginEditor.h": "struct Editor {};\n"},
         "no page files (.html, .htm, .js, .mjs, .ts, .tsx, .jsx) found"),
    ],
    ids=["page only", "C++ only"],
)
def test_paths_with_no_cpp_or_no_page_files_are_a_usage_error(tmp_path, present, message):
    # Given a folder that holds only one side of the editor
    for name, text in present.items():
        write(tmp_path / name, text)

    # When the binding check runs on it
    result = run_check(tmp_path)

    # Then it prints usage and what is missing, and exits with the usage-error code
    assert result.returncode == 2, result.stdout + result.stderr
    assert "usage:" in result.stderr
    assert message in result.stderr


# Interface


def test_tilt_eq_example_passes_the_binding_check():
    # Given the tilt-EQ example's JUCE wrapper: its editor sources and its UI folder

    # When the binding check runs on them
    result = run_check(EXAMPLE_JUCE / "Source", EXAMPLE_JUCE / "ui")

    # Then its tilt relay and tilt state match, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_juce_webview_demo_layout_passes_with_computed_name_warnings(tmp_path):
    # Given the layout of JUCE's WebView plugin demo: literal relays of all three
    # classes in the editor, and a React TypeScript page whose control components
    # request their state from an identifier prop
    write(
        tmp_path / "WebViewPluginDemo.h",
        "class WebViewPluginAudioProcessorEditor : public AudioProcessorEditor {\n"
        '    WebSliderRelay       cutoffSliderRelay    { "cutoffSlider" };\n'
        '    WebToggleButtonRelay muteToggleRelay      { "muteToggle" };\n'
        '    WebComboBoxRelay     filterTypeComboRelay { "filterTypeCombo" };\n'
        "};\n",
    )
    app = tmp_path / "WebViewPluginDemoGUI" / "src" / "App.tsx"
    write(
        app,
        'import * as Juce from "@juce-framework/webview";\n'
        "function JuceSlider({ identifier, title }: { identifier: string; title: string }) {\n"
        "  const sliderState = Juce.getSliderState(identifier);\n"
        "  return <Slider aria-label={title} />;\n"
        "}\n"
        "function JuceCheckbox({ identifier }: { identifier: string }) {\n"
        "  const checkboxState = Juce.getToggleState(identifier);\n"
        "  return <Checkbox />;\n"
        "}\n"
        "function JuceComboBox({ identifier }: { identifier: string }) {\n"
        "  const comboBoxState = Juce.getComboBoxState(identifier);\n"
        "  return <Select />;\n"
        "}\n"
        "function App() {\n"
        "  return (<div>\n"
        '    <JuceSlider identifier="cutoffSlider" title="Cutoff" />\n'
        '    <JuceCheckbox identifier="muteToggle" />\n'
        '    <JuceComboBox identifier="filterTypeCombo" />\n'
        "  </div>);\n"
        "}\n",
    )
    write(tmp_path / "WebViewPluginDemoGUI" / "src" / "global.d.ts", 'declare module "*.css";\n')

    # When the binding check runs on the demo header and its GUI folder
    result = run_check(tmp_path / "WebViewPluginDemo.h", tmp_path / "WebViewPluginDemoGUI")

    # Then each relay type gives one computed-name warning, and the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{app}:3: warning: relay-name: getSliderState names are computed in the page,"
        " so WebSliderRelay names can't be matched",
        f"{app}:7: warning: relay-name: getToggleState names are computed in the page,"
        " so WebToggleButtonRelay names can't be matched",
        f"{app}:11: warning: relay-name: getComboBoxState names are computed in the page,"
        " so WebComboBoxRelay names can't be matched",
    ]


def test_plugin_freedom_system_layout_passes_with_a_computed_name_warning(tmp_path):
    # Given the layout of a Plugin Freedom System editor: relay pointers declared
    # several per line and created through make_unique, and a page that requests
    # the slider states in a loop over a list of ids and the toggle by literal name
    write(
        tmp_path / "Source" / "PluginEditor.h",
        "class PluginEditor : public juce::AudioProcessorEditor {\n"
        "    std::unique_ptr<juce::WebSliderRelay> gainRelay, toneRelay, mixRelay;\n"
        "    std::unique_ptr<juce::WebToggleButtonRelay> bypassRelay;\n"
        "    std::unique_ptr<juce::WebBrowserComponent> webView;\n"
        "};\n",
    )
    write(
        tmp_path / "Source" / "PluginEditor.cpp",
        "PluginEditor::PluginEditor (PluginProcessor& p) : AudioProcessorEditor (&p) {\n"
        '    gainRelay = std::make_unique<juce::WebSliderRelay> ("gain");\n'
        '    toneRelay = std::make_unique<juce::WebSliderRelay> ("tone");\n'
        '    mixRelay = std::make_unique<juce::WebSliderRelay> ("mix");\n'
        '    bypassRelay = std::make_unique<juce::WebToggleButtonRelay> ("bypass");\n'
        "}\n",
    )
    page = tmp_path / "Source" / "ui" / "public" / "js" / "index.js"
    write(
        page,
        'import { getSliderState, getToggleState } from "./juce/index.js";\n'
        'const SLIDER_IDS = ["gain", "tone", "mix"];\n'
        'document.addEventListener("DOMContentLoaded", () => {\n'
        "  SLIDER_IDS.forEach((id) => {\n"
        "    const state = getSliderState(id);\n"
        "    state.valueChangedEvent.addListener(() => render(id, state));\n"
        "  });\n"
        '  const bypass = getToggleState("bypass");\n'
        "});\n",
    )

    # When the binding check runs on the editor folder
    result = run_check(tmp_path / "Source")

    # Then the slider loop gives one computed-name warning, the toggle matches, and
    # the check passes
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"{page}:5: warning: relay-name: getSliderState names are computed in the page,"
        " so WebSliderRelay names can't be matched"
    ]
