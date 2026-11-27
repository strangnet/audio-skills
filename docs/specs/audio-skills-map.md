# Capability map: strangnet-audio-skills

Source: shape session, 2026-11-26

**What it's for:** turn a plugin idea into a working VST3/AU/CLAP plugin, an MPC VST, or both, using any common AI agent. The skills hold only audio and plugin know-how and leave the workflow to the user. The package sits alongside `strangnet-skills` and never duplicates it.

| Id | Responsibility | Depends on |
|---|---|---|
| foundation | Repo skeleton (manifests, sync, CI, evals); tilt-EQ example (core + JUCE wrapper + MPC wrapper); skills `audio-portable-core`, `audio-dsp`, `audio-parameters`; core-purity and real-time checkers | — |
| juce | Skills `audio-juce` (JUCE 9.0.x; VST3/AU, and CLAP through clap-juce-extensions) and `audio-juce-webview` (WebView UI, binding checker); curated JUCE 9 patterns from the Plugin Freedom System | foundation |
| mpc | Skill `audio-mpc`: finds the SDK, calls its tools with absolute paths and `--dir <project>`, reads Akai's skills for facts only | foundation |
| validation | Skill `audio-validation`: pluginval, clap-validator, auval, DAW checklist, installing and clearing plugin caches (macOS) | juce |
| troubleshooting | Skill `audio-troubleshooting`: curated solved-problem knowledge base, search, saving new solutions to the project's own log | juce, mpc |
| packaging | Skill `audio-packaging`: Developer ID signing, notarization, stapling, `.pkg` | validation |
| windows | Windows sections across every skill (paths, caches, toolchain, installer, WebView2) | packaging |

Candidate, not yet placed in the build order:

| Id | Responsibility | Depends on |
|---|---|---|
| dsp-recipes | Skill `audio-dsp-recipes`: one reference per DSP technique (filters, dynamics, delay and reverb, saturation, oscillators and envelopes, granular), building on `audio-dsp`'s rules. Neither the Plugin Freedom System nor the map covers techniques; decide after the M2/M4 run shows whether agents get them wrong | foundation |

Build order: foundation → juce → mpc → validation → troubleshooting → packaging → windows

## Accepted trade-offs that apply to more than one capability

- **The first MPC build needs network access and write access to the SDK folder.** The SDK's build tool downloads zig into the SDK the first time it runs, so sandboxed agents can't do that run. The user does it once.
- **`audio-mpc` doesn't work fully when installed alone.** It needs the SDK by nature, so without it, it can only state the MPC constraints and explain how to get the SDK. This is a stated exception to the rule that skills work when installed alone.
- **Evals can't build plugins.** The eval sandbox blocks downloads and toolchains. Evals check that skills fire and what they advise; real builds are checked locally.
