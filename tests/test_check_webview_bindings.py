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
         "no page files (.html, .htm, .js, .mjs) found"),
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
