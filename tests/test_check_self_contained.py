"""Self-containment check: every relative Markdown link in a skill's .md files must
resolve to an existing file inside that skill's own folder."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_self_contained.py"


def write(path, text=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run_check(root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True
    )


# Zero


def test_passes_when_there_are_no_skills(tmp_path):
    # Given a repo with no skills folder

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it passes
    assert result.returncode == 0, result.stdout + result.stderr


def test_passes_when_a_skill_has_no_links(tmp_path):
    # Given a skill whose SKILL.md has no links
    write(tmp_path / "skills" / "audio-dsp" / "SKILL.md", "# DSP\nNo links here.\n")

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it passes
    assert result.returncode == 0, result.stdout + result.stderr


# One


def test_passes_when_link_points_to_existing_file_inside_skill(tmp_path):
    # Given a skill that links to its own reference file
    skill = tmp_path / "skills" / "audio-dsp"
    write(skill / "references" / "realtime.md", "# Real-time rules\n")
    write(skill / "SKILL.md", "# DSP\nSee [rules](references/realtime.md).\n")

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it passes
    assert result.returncode == 0, result.stdout + result.stderr


def test_fails_with_file_line_and_target_when_link_escapes_skill_folder(tmp_path):
    # Given a skill that links to a shared file at the repo root on line 3
    write(tmp_path / "references" / "juce" / "patterns.md", "# Patterns\n")
    write(
        tmp_path / "skills" / "audio-juce" / "SKILL.md",
        "# JUCE\n\nSee [patterns](../../references/juce/patterns.md).\n",
    )

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it fails, reporting the file, the line and the link target
    assert result.returncode == 1
    assert "skills/audio-juce/SKILL.md:3" in result.stdout
    assert "../../references/juce/patterns.md" in result.stdout


def test_fails_when_link_points_to_missing_file_inside_skill(tmp_path):
    # Given a skill that links to a reference file it doesn't contain
    write(tmp_path / "skills" / "audio-dsp" / "SKILL.md", "See [rules](references/gone.md).\n")

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it fails, reporting the broken link
    assert result.returncode == 1
    assert "skills/audio-dsp/SKILL.md:1" in result.stdout
    assert "references/gone.md" in result.stdout


# Many


def test_reports_every_bad_link_across_files_and_skills(tmp_path):
    # Given two skills with bad links in different files
    write(tmp_path / "skills" / "audio-dsp" / "SKILL.md", "[a](../x.md)\n[b](gone.md)\n")
    write(
        tmp_path / "skills" / "audio-parameters" / "references" / "state.md",
        "[c](../../audio-dsp/SKILL.md)\n",
    )

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it fails and reports all three
    assert result.returncode == 1
    assert "skills/audio-dsp/SKILL.md:1" in result.stdout
    assert "skills/audio-dsp/SKILL.md:2" in result.stdout
    assert "skills/audio-parameters/references/state.md:1" in result.stdout


# Boundaries


def test_passes_when_link_goes_up_and_stays_inside_skill(tmp_path):
    # Given a reference file that links back up to its skill's SKILL.md
    skill = tmp_path / "skills" / "audio-dsp"
    write(skill / "SKILL.md", "# DSP\n")
    write(skill / "references" / "realtime.md", "Back to [the skill](../SKILL.md).\n")

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it passes
    assert result.returncode == 0, result.stdout + result.stderr


def test_fails_when_link_is_an_absolute_path(tmp_path):
    # Given a skill that links to an absolute path
    write(tmp_path / "skills" / "audio-dsp" / "SKILL.md", "See [hosts](/etc/hosts).\n")

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it fails, reporting the link as outside the skill
    assert result.returncode == 1
    assert "link outside skill: /etc/hosts" in result.stdout


# Interface


def test_ignores_urls_mailto_and_pure_anchors(tmp_path):
    # Given a skill whose only links are URLs, a mailto link and an anchor
    write(
        tmp_path / "skills" / "audio-dsp" / "SKILL.md",
        "[docs](https://juce.com/learn)\n"
        "[spec](http://example.com/a)\n"
        "[mail](mailto:someone@example.com)\n"
        "[below](#real-time-rules)\n",
    )

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it passes
    assert result.returncode == 0, result.stdout + result.stderr


def test_checks_the_file_part_of_a_link_with_an_anchor(tmp_path):
    # Given one link to a section of an existing file and one to a missing file
    skill = tmp_path / "skills" / "audio-dsp"
    write(skill / "references" / "realtime.md", "# Real-time rules\n## Locks\n")
    write(
        skill / "SKILL.md",
        "[locks](references/realtime.md#locks)\n[gone](references/gone.md#intro)\n",
    )

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then only the link to the missing file is reported
    assert result.returncode == 1
    assert "references/realtime.md#locks" not in result.stdout
    assert "broken link: references/gone.md#intro" in result.stdout


def test_ignores_links_inside_code_fences_and_inline_code(tmp_path):
    # Given link syntax that appears only in a code fence and in inline code
    write(
        tmp_path / "skills" / "audio-dsp" / "SKILL.md",
        "Write links like `[text](../other.md)` in your own docs.\n"
        "```markdown\n"
        "[example](../../outside.md)\n"
        "```\n"
        "~~~\n"
        "[another](/abs/path.md)\n"
        "~~~\n",
    )

    # When the self-containment check runs
    result = run_check(tmp_path)

    # Then it passes
    assert result.returncode == 0, result.stdout + result.stderr
