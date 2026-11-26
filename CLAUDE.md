# strangnet audio skills

> **Scope:** this file is for agents working on this repository. It is not a template for other projects; the reusable parts are the skills in `skills/`. For what each skill does and how users install them, see `README.md`.

This package holds audio-plugin **know-how** only (real-time DSP, parameters, JUCE, MPC). It sits alongside `strangnet-skills` and never duplicates it, and it never prescribes a workflow. Terms are defined in `GLOSSARY.md`; specs live in `docs/specs/`.

## Layout

- `skills/<skill>/SKILL.md`: one folder per skill, named `audio-*`, with its own `references/` and, for skills that own a checker, `scripts/`. Keep the layout flat, with no category folders: several harnesses only discover skills in direct subfolders of `skills/`.
- `references/<set>/`: shared reference sets, vendored into the skills that opt in.
- `examples/`: example plugins used to prove the skills end to end. They don't ship inside any skill.
- `evals/plugin/`: behavioural evals for `claude plugin eval`.
- `scripts/`: repo tooling (sync, version and self-containment checks). `tests/`: pytest tests for repo tooling and checkers.
- Manifests: `.claude-plugin/plugin.json` (source of truth; Claude Code and Copilot read it), `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`. The Claude marketplace entry lives in the `strangnet` marketplace in the agent-skills repo, without a version.

## Rules

- **Know-how, not workflow.** A skill states facts, rules and pitfalls. It never prescribes step order, planning templates or state files; the user brings their own process.
- **Skills are self-contained.** A skill must work when installed alone (skills.sh copies single folders). Never link from a skill to a file outside its own folder. Edit shared reference files only under the root `references/`, then run `scripts/sync-references.sh`. The one stated exception is `audio-mpc`, which needs the user's Akai SDK clone by nature.
- **Skills are harness-neutral.** Write for Claude Code, Codex, Copilot, pi and skills.sh installs alike.
- **Frontmatter:** `name` matches the folder; `description` says what the skill does, then "Use when ..." with concrete triggers, then "Not for ..." lines that hand off to Akai's `mpc-plugin-*` skills inside an SDK checkout and exclude agent-plugin topics.
- **Keep `SKILL.md` short.** Move detail into `references/` that the skill reads only when needed.
- **Version-sensitive facts cite their source** (JUCE version, SDK document) and pin the version.
- **Checkers** are Python 3 using only the standard library, read source code only, print `file:line: severity: rule: message`, and exit 0 (no errors), 1 (errors) or 2 (usage error). Their tests use pytest.
- **Adding, renaming or removing a skill** also means updating the Skills table in `README.md`, eval cases under `evals/plugin/` and its README table, and Credits if the skill derives from someone else's work. Manifests need no change.
- **Versions:** every manifest in this repo carries the same version. Don't bump versions in feature PRs unless asked.

## Checks

Run these before calling a change done (CI runs all but the last):

```bash
uv run pytest                              # repo tooling and checker tests
scripts/sync-references.sh --check         # vendored references match references/
uv run scripts/check_versions.py .         # all manifests share one version
uv run scripts/check_self_contained.py .   # no skill links outside its folder
claude plugin validate .                   # manifests and skills load
```

Evals cost money and time; run them only when asked or when a skill's behaviour changed. See `evals/plugin/README.md`.

## Writing style

Plain, direct prose in skills and docs. Short sentences, active voice, concrete examples. Use British or American spelling consistently within a file.
