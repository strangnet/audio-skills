---
tags: [audio-mpc, install]
max_turns: 30
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---
`my-plugin/` is my MPC effect, Grit, kept in my own repo, not inside Akai's SDK. My clone of Akai's MPC Plugin SDK is at `./mpc-sdk`. I built it earlier and the build, validation and host simulator all passed. Can you check the build output in `my-plugin/build/` is complete (both ARM libraries, the manifest, the version file and the skins) and tell me where everything is?
