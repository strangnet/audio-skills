# 09: audio-portable-core gives the right advice and stays quiet when it should

Status: done
Spec: [foundation](../../foundation.md)
Blocked by: 06

## Delivers
The `audio-portable-core` skill: a `SKILL.md` whose description has "Use when" and "Not for" lines, plus references, alongside the core-purity checker it already holds. Its eval cases include the two shared negative cases for Claude Code and Cowork plugins.

## Scenarios
- Portable core: a share-DSP prompt → fires, with every advice item (header-only, standard library only, relative include from the wrapper's `src/`, no host types, real-time marker, parameter ids defined once, run the core-purity checker)
- Portable core: a desktop-only prompt → doesn't fire
- Portable core: a Claude Code plugin prompt → no `audio-*` skill fires
- Portable core: a Cowork plugin prompt → no `audio-*` skill fires
- Portable core: inside an SDK checkout on an MPC-only plugin → doesn't fire (a stand-in scaffold)
