# SDK edge cases: no SDK, builds that write into it, failures, fixes and a changed SDK

`<sdk>` is the SDK clone and `<project>` the folder holding the plugin's `plugin.json` and `src/`, both as absolute paths. Checked against the SDK at commit `e78bad5`. Each section names the files its facts come from.

## No SDK found, or none at all

- `$MPC_SDK` unset, or naming a folder without `tools/build.py`: ask the user where their clone is. Don't look for it with `find`, `mdfind`, `locate`, `fd` or by listing home and system folders, and don't clone it on your own.
- No clone at all: nothing can be built, validated or tested, but the MPC's hard rules still apply, so state them. To get the SDK, the user clones `https://github.com/inmusic-software/mpc-plugin-builder-sdk` to a folder outside their project and sets `MPC_SDK` to its absolute path in their shell profile. It needs Python 3.9 or later; everything else, zig included, comes on the first build or from the user's own toolchain.
- The SDK's `GETTING_STARTED.md` shows a placeholder clone URL (`<org>/mpc-plugin-sdk`); use inMusic's repository above.
- Clone only after the user's yes, and only to the folder they choose.

Source: `README.md` ("Requirements"), `GETTING_STARTED.md`.

## Builds that write into the SDK

The build tool writes into `<sdk>/.sdk-tools/` in two cases. Both can happen on a build the user expects to be routine.

**The host simulator.** On the parameter-dump step, the build compiles `tools/host-sim/host_sim.cpp` into `<sdk>/.sdk-tools/host_sim` when that binary is missing, or older than either `tools/host-sim/host_sim.cpp` or `framework/mpc_vst2_abi.h`. So it happens on the first build with a clone, and again after an SDK update (a `git pull`) that touched either file. It happens under every toolchain: with zig it compiles with zig, otherwise with the system C++ compiler.

**zig, under the default `--toolchain zig`.** Every build looks for a working zig, in this order:
1. `--zig PATH`
2. `$ZIG`
3. `zig` on `PATH`
4. `<sdk>/.sdk-tools/zigenv`, from an earlier install

`--zig` and `$ZIG` take a zig executable or a Python interpreter that has the `ziglang` package. A candidate that doesn't run is skipped with a warning. When none works, the build creates a Python virtual environment at `<sdk>/.sdk-tools/zigenv` and installs `ziglang` into it with pip: a one-time download of about 50 MB, so it needs network access as well as write access.

**What a failed write looks like.**
- `<sdk>` not writable and no `.sdk-tools/` yet: the build stops with a Python traceback ending in `PermissionError: [Errno 13] Permission denied: '<sdk>/.sdk-tools'`. With no zig found it stops before compiling anything; with zig found it stops after the native build, at "building host_sim (first use)". The build tool doesn't catch this error, so no `ERROR:` summary follows.
- `.sdk-tools/` exists but isn't writable: the build warns that building host_sim failed and skips the parameter dump, so `<project>/build/params.json` is missing or left from an earlier build.
- No network while installing zig: the build stops with "pip install ziglang failed" and the tool's list of other ways to get zig.

**The hand-off.** When the agent can't write to `<sdk>` or reach the network:
- Don't work around it. No `chmod` or `sudo` on the SDK, no copy of the SDK to a writable place, no host simulator compiled elsewhere, no edits to the build tool, and no switch of toolchain to dodge the write (the host simulator is still built into the SDK).
- Hand that one run to the user. Give the exact command, with absolute paths, for example `python3 "<sdk>/tools/build.py" "<project>"`. Say that it compiles the host simulator into `<sdk>/.sdk-tools/` and, with no zig on `PATH`, in `$ZIG` or passed with `--zig`, downloads zig into `<sdk>/.sdk-tools/zigenv`. If the user has zig already, `--zig` or `ZIG` avoids the download.
- After that run, later builds write nothing into the SDK until an SDK update touches the host simulator's sources, so the agent can take over again.

Python's bytecode cache is the only other write into the SDK, and it fails silently without harm.

Source: `tools/build.py` (`find_zig`, `zig_install_help`, `Builder.__init__`, `Builder.ensure_host_sim`, `main`), `docs/building.md` ("Toolchain: zig").

## Failures

- The host simulator's exit codes: 0 pass (warnings allowed), 1 at least one `FAIL`, 2 the plugin crashed. Any `FAIL` line, or a crash, is a failed check. So is a validation `ERROR` and a build that exits non-zero.
- A failed check means the plugin isn't done, even when the build, validation and every other test passed. Report the check that failed: quote the `FAIL` line and the report section it sits in (for example "Main render"), and the crash phase for exit 2.
- `<sdk>/docs/troubleshooting.md` ("Host simulator problems") and Akai's `mpc-plugin-troubleshoot` skill give the usual cause of each `FAIL`. Read them by absolute path.

Source: `tools/host-sim/README.md` ("Reading the report"), `docs/install-and-test.md`, `docs/troubleshooting.md`.

## Fixes

- The fix goes in the project: its sources in `src/`, `plugin.json`, `ui.json` or `Content/`. Compiler errors often point into `<sdk>/framework/mpc_plugin.h`; the SDK's troubleshooting document says these usually mean the plugin calls the framework wrongly.
- Never edit, patch, replace or "temporarily" change SDK files (framework headers, tools, templates, the tool cache). The SDK is shared by every plugin built with it, and an update overwrites the change.
- Look the error up in `<sdk>/docs/troubleshooting.md` ("Build problems") and `mpc-plugin-troubleshoot` first, and apply the fix they give to the project.
- If the SDK itself looks wrong, tell the user, and leave the decision (update the clone, report it to Akai) to them.
- After a fix, rebuild and run the host simulator again. The plugin is done only when both pass.

Source: `docs/troubleshooting.md` ("Build problems"), `.agents/skills/mpc-plugin-troubleshoot/SKILL.md`.

## A changed SDK

The skill's facts are a summary checked against commit `e78bad5`. The SDK keeps changing, and the user's clone may be newer.

- When the found SDK's document states a fact differently from this skill, follow the document.
- Say that the SDK has changed since commit `e78bad5`, which this skill was checked against. Name the document and give both values, so the user can see the change.
- `<sdk>/docs/changelog.md` lists what changed. `git -C "<sdk>" log --oneline -1` shows which commit the clone is at, without changing anything.
- An example: at `e78bad5`, a 32-bit or 64-bit MPC needs MPC OS 3.10.1 or later, with Preferences → Enhancements (Beta) → Enable Enhancements and External Plugin Support on, and the MPC Sample needs firmware v1.4.0 or later with MIDI Config → Dev Enhancements (Beta) → Custom Plug-In Support on. A clone whose `docs/supported-devices.md` names another minimum wins, and the user hears that it changed.

Source: `docs/supported-devices.md` ("Side by side"), `README.md` ("Requirements"), `docs/changelog.md`.
