#!/usr/bin/env python3
"""Check that every skill is self-contained.

Each skill must work when copied on its own (skills.sh installs single skill
folders), so every relative Markdown link in a skill's .md files must resolve
to an existing file inside that skill's folder. URLs, mailto links and pure
anchors are ignored, as are links inside code fences and inline code.

    scripts/check_self_contained.py <repo-root>    exit 1 on any bad link (for CI)
"""

import re
import sys
from collections.abc import Iterator
from pathlib import Path

LINK = re.compile(r"\]\(([^)\s]+)\)")
SCHEME = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*:")
FENCE = re.compile(r"\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")


def links_in(text: str) -> Iterator[tuple[int, str]]:
    """Yield (line number, link target) for every link outside code."""
    fence = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        marker = FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif marker.group(1) == fence:
                fence = None
            continue
        if fence is None:
            for target in LINK.findall(INLINE_CODE.sub("", line)):
                yield lineno, target


def problem_with(target: str, md: Path, skill_dir: Path) -> str | None:
    if SCHEME.match(target) or target.startswith("#"):
        return None
    resolved = (md.parent / target.split("#", 1)[0]).resolve()
    if not resolved.is_relative_to(skill_dir):
        return "link outside skill"
    if not resolved.exists():
        return "broken link"
    return None


def main(root: Path) -> int:
    status = 0
    for skill in sorted(p for p in (root / "skills").glob("*") if p.is_dir()):
        skill_dir = skill.resolve()
        for md in sorted(skill.glob("**/*.md")):
            for lineno, target in links_in(md.read_text()):
                problem = problem_with(target, md, skill_dir)
                if problem:
                    print(f"{md.relative_to(root)}:{lineno}: {problem}: {target}")
                    status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
