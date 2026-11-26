"""Sync check: a skill's copy of a shared reference set must match the root set."""

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "sync-references.sh"


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "scripts").mkdir()
    shutil.copy(SCRIPT, tmp_path / "scripts" / SCRIPT.name)
    shared = tmp_path / "references" / "juce"
    shared.mkdir(parents=True)
    (shared / "patterns.md").write_text("# Patterns\n")
    copy = tmp_path / "skills" / "audio-juce" / "references" / "juce"
    copy.mkdir(parents=True)
    (copy / "patterns.md").write_text("# Patterns\n")
    return tmp_path


def run_check(root):
    return subprocess.run(
        ["bash", str(root / "scripts" / SCRIPT.name), "--check"],
        capture_output=True,
        text=True,
    )


def test_check_passes_when_skill_copy_matches_root_set(repo):
    # Given a skill whose copy of the shared set matches the root set (fixture)

    # When the sync check runs
    result = run_check(repo)

    # Then it passes
    assert result.returncode == 0, result.stdout + result.stderr


def test_check_fails_and_names_the_copy_when_skill_copy_was_edited(repo):
    # Given a skill whose copy of the shared set was edited
    copy = repo / "skills" / "audio-juce" / "references" / "juce" / "patterns.md"
    copy.write_text("# Patterns\nedited only here\n")

    # When the sync check runs
    result = run_check(repo)

    # Then it fails and names the drifted copy
    assert result.returncode == 1
    assert "skills/audio-juce/references/juce" in result.stdout
