#!/usr/bin/env python3
"""Check that every plugin manifest in this repo declares the same version.

.claude-plugin/plugin.json is the source of truth (Claude Code and Copilot read
it). The Codex plugin manifest and this plugin's entry in the Codex marketplace
must match it, because clients compare versions to decide whether an installed
copy needs updating. The `strangnet` Claude marketplace lives in the agent-skills
repo and lists this plugin without a version, so it isn't checked here.

    scripts/check_versions.py <repo-root>    exit 1 if any manifest differs (for CI)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SOURCE = ".claude-plugin/plugin.json"
CODEX_MANIFEST = ".codex-plugin/plugin.json"
CODEX_MARKETPLACE = ".agents/plugins/marketplace.json"


class ManifestMissing(Exception):
    pass


def read(root: Path, relpath: str) -> dict:
    path = root / relpath
    if not path.is_file():
        raise ManifestMissing(relpath)
    return json.loads(path.read_text())


def main(root: Path) -> int:
    try:
        return check(root)
    except ManifestMissing as missing:
        print(f"{missing} is missing")
        return 1


def check(root: Path) -> int:
    source = read(root, SOURCE)
    expected = source.get("version")
    name = source["name"]
    if expected is None:
        print(f"{SOURCE} is missing a version field")
        return 1
    if not re.fullmatch(r"\d+\.\d+\.\d+", expected):
        print(f"{SOURCE} has version {expected}; expected MAJOR.MINOR.PATCH")
        return 1

    status = 0
    found = {CODEX_MANIFEST: read(root, CODEX_MANIFEST)["version"]}
    entry = next(
        (e for e in read(root, CODEX_MARKETPLACE)["plugins"] if e["name"] == name), None
    )
    if entry is None:
        print(f"{CODEX_MARKETPLACE} has no entry for plugin {name}")
        status = 1
    else:
        found[CODEX_MARKETPLACE] = entry["version"]

    for manifest, version in found.items():
        if version != expected:
            print(f"{manifest} has version {version}; expected {expected} (from {SOURCE})")
            status = 1
    if status == 0:
        print(f"All plugin manifests use version {expected}.")
    return status


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
