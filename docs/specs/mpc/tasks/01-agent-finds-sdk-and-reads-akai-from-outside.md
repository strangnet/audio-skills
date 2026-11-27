# 01: The agent finds the SDK and reads Akai's material from outside the project (M2)

Status: done
Spec: [mpc](../../mpc.md)
Blocked by: none

## Delivers
A smoke run settles the spec's eval assumptions: whether stand-in Akai skills in the stand-in SDK are discovered as real skills, whether `$MPC_SDK` reaches the agent from the shell or through a scaffold, and which working folder a run uses. The `audio-mpc` skill exists with its final frontmatter and its sections on finding the SDK, calling the SDK's tools from outside the checkout, and reading Akai's skills and documents for facts only. The stand-in SDK scaffold exists (stub build, validation and scaffolding tools, stub host simulator, documents, stand-in Akai skills), and the External SDK (M2) eval case is written. The README lists the skill, and the eval README says to unset `MPC_SDK` before a run.

## Scenarios
- `audio-mpc` fires on building, testing, validating or fixing an MPC plugin in a project outside an SDK checkout
- `$MPC_SDK` names a folder that holds the SDK's build tool → the agent uses it
- the user names the SDK's folder → the agent uses it after checking it holds the build tool
- the agent calls an SDK tool (absolute paths, the project as an argument, where output and caches go, never copying between project and SDK)
- the SDK is found → the agent reads the SDK's document or Akai's skill for a topic by absolute path
- reading Akai's skills → facts and hard rules kept, workflow left out

## Smoke run findings

A throwaway case (`audio-mpc-smoke`, deleted afterwards) ran three times with Claude Code 2.1.332: `claude plugin eval . --scaffold --allow-tools Bash Write Edit --no-publish --runs 1 --ablation none --case audio-mpc-smoke --keep-temp`, twice under `env -u MPC_SDK` and once with `MPC_SDK=/leak/test/from-shell` exported. Its scaffold wrote stand-in `mpc-plugin-test` skills to `mpc-sdk/.claude/skills/` and `mpc-sdk/.agents/skills/`, a `.claude/settings.json` with `{"env": {"MPC_SDK": "/smoke/from-project-settings"}}` in the working folder, and (third run) a project skill at `.claude/skills/smoke-root-skill/`. The prompt had the agent print `pwd`, `$MPC_SDK`, `$HOME` and the scaffold's own notes, list its skills, read `mpc-sdk/README.md` and the stand-in `SKILL.md` by path, and list its skills again.

- **(a) Stand-in skills aren't discovered.** Neither `mpc-sdk/.claude/skills/mpc-plugin-test` nor `mpc-sdk/.agents/skills/mpc-plugin-test` appeared in the run's skill list (the trace's `system/init` `skills` field) or later in the session, even after the agent read the stand-in `SKILL.md` by path. A project skill at the working folder's own `.claude/skills/` wasn't discovered either: the runner doesn't load project-level settings or skills. The assumption holds, so the stand-in keeps both copies, as the real SDK does, and the M2 case keeps the grader that forbids a skill-tool call to them.
- **(b) Project settings don't reach the agent.** With `.claude/settings.json` setting `MPC_SDK` in the working folder, the agent's shell printed `MPC_SDK=[]`. A scaffold can't set `$MPC_SDK`, so the `$MPC_SDK` rule stays covered by inspection, and the cases name the SDK in the prompt.
- **(c) Working folder.** The agent's working folder is `<run temp>/home/cwd` (for example `/private/tmp/e-SLwnxm/home/cwd`), and `$HOME` is `<run temp>/home`. The scaffold runs in that same folder, so everything it writes, including `mpc-sdk/` and `my-plugin/`, lands inside the run's temporary folder. The scaffold's `$0` and `BASH_SOURCE` are the absolute path of `scaffold.sh` in the repo, so a case's scaffold can source a shared helper next to it (`../_shared/…`); the smoke run did. Only the `scaffold_script` path itself must stay inside the case folder.
- **Leak test.** With `MPC_SDK` exported in the shell that ran the eval, both the scaffold and the agent saw it unset: the runner doesn't pass it through. Unsetting it with `env -u MPC_SDK` is kept in the eval README anyway, as cheap insurance against a runner that does.
