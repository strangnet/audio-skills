# 01: The repo is a valid, empty plugin with CI

Status: done
Spec: [foundation](../../foundation.md)
Blocked by: none

## Delivers
`strangnet-audio-skills` exists as a valid plugin with no skills yet, at version 0.1.0:
- a Claude plugin manifest, a Codex plugin manifest and a Codex marketplace
- `AGENTS.md` as a symlink to `CLAUDE.md`, which holds the authoring conventions
- a root `references/` folder with a sync script
- an `evals/plugin/` layout
- an MIT license

CI runs four checks: the version check across the three manifests, the sync check, the self-containment check and `claude plugin validate`.

## Scenarios
- Install: this repo's manifests disagree on the version → CI's version check fails
- Install: a shared reference file was edited only in a skill's copy → CI's sync check fails
- Install: one skill folder copied alone → every file it refers to is inside that folder (the self-containment check)
- Reader: the repo's license is MIT, matching `agent-skills`
