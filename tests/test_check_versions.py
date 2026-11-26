"""Version check: the Claude plugin manifest, the Codex plugin manifest and the
Codex marketplace entry must declare the same MAJOR.MINOR.PATCH version."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_versions.py"
PLUGIN = "strangnet-audio-skills"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def write_manifests(root, claude="0.1.0", codex=None, marketplace=None):
    """Write the three manifests; codex and marketplace default to the claude version."""
    codex = claude if codex is None else codex
    marketplace = claude if marketplace is None else marketplace
    write_json(root / ".claude-plugin" / "plugin.json", {"name": PLUGIN, "version": claude})
    write_json(root / ".codex-plugin" / "plugin.json", {"name": PLUGIN, "version": codex})
    write_json(
        root / ".agents" / "plugins" / "marketplace.json",
        {"name": PLUGIN, "plugins": [{"name": PLUGIN, "version": marketplace}]},
    )


@pytest.fixture
def repo(tmp_path):
    write_manifests(tmp_path)
    return tmp_path


def run_check(root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True
    )


# Zero / One / Many


def test_passes_and_prints_version_when_all_three_manifests_agree(repo):
    # Given three manifests that all declare 0.1.0 (fixture)

    # When the version check runs
    result = run_check(repo)

    # Then it passes and prints the shared version
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0.1.0" in result.stdout


def test_fails_naming_file_and_both_versions_when_codex_manifest_differs(repo):
    # Given the Codex plugin manifest lags behind at 0.0.9
    write_manifests(repo, codex="0.0.9")

    # When the version check runs
    result = run_check(repo)

    # Then it fails, naming the file, its version and the expected version
    assert result.returncode == 1
    assert ".codex-plugin/plugin.json" in result.stdout
    assert "0.0.9" in result.stdout
    assert "0.1.0" in result.stdout


def test_fails_when_codex_marketplace_entry_differs(repo):
    # Given the Codex marketplace entry for the plugin lags behind at 0.0.9
    write_manifests(repo, marketplace="0.0.9")

    # When the version check runs
    result = run_check(repo)

    # Then it fails, naming the marketplace file
    assert result.returncode == 1
    assert ".agents/plugins/marketplace.json" in result.stdout


def test_reports_every_manifest_that_differs(repo):
    # Given both Codex files lag behind the source manifest
    write_manifests(repo, codex="0.0.9", marketplace="0.0.8")

    # When the version check runs
    result = run_check(repo)

    # Then it fails and reports both files
    assert result.returncode == 1
    assert ".codex-plugin/plugin.json has version 0.0.9" in result.stdout
    assert ".agents/plugins/marketplace.json has version 0.0.8" in result.stdout


# Boundaries


@pytest.mark.parametrize("version", ["0.1", "v0.1.0", "0.1.0-beta"])
def test_fails_when_source_version_is_not_major_minor_patch(repo, version):
    # Given every manifest agrees on a version that isn't MAJOR.MINOR.PATCH
    write_manifests(repo, claude=version)

    # When the version check runs
    result = run_check(repo)

    # Then it fails and says the format is wrong
    assert result.returncode == 1
    assert "MAJOR.MINOR.PATCH" in result.stdout


# Exceptions


def test_fails_when_source_manifest_has_no_version(repo):
    # Given the Claude plugin manifest has no version field
    write_json(repo / ".claude-plugin" / "plugin.json", {"name": PLUGIN})

    # When the version check runs
    result = run_check(repo)

    # Then it fails cleanly, naming the manifest, without a traceback
    assert result.returncode == 1
    assert ".claude-plugin/plugin.json is missing a version" in result.stdout
    assert "Traceback" not in result.stderr


def test_fails_when_codex_marketplace_has_no_entry_for_the_plugin(repo):
    # Given the Codex marketplace lists only some other plugin
    write_json(
        repo / ".agents" / "plugins" / "marketplace.json",
        {"name": PLUGIN, "plugins": [{"name": "other-plugin", "version": "0.1.0"}]},
    )

    # When the version check runs
    result = run_check(repo)

    # Then it fails cleanly, saying the entry is missing
    assert result.returncode == 1
    assert f".agents/plugins/marketplace.json has no entry for plugin {PLUGIN}" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "manifest",
    [".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".agents/plugins/marketplace.json"],
)
def test_fails_naming_the_file_when_a_manifest_is_missing(repo, manifest):
    # Given one of the three manifests doesn't exist
    (repo / manifest).unlink()

    # When the version check runs
    result = run_check(repo)

    # Then it fails cleanly, naming the missing file
    assert result.returncode == 1
    assert f"{manifest} is missing" in result.stdout
    assert "Traceback" not in result.stderr
