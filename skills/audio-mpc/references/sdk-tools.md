# Calling the SDK's tools from outside the checkout

Every command below uses absolute paths: `<sdk>` is the SDK clone, `<project>` is the folder holding the plugin's `plugin.json` and `src/`. Quote both, since plugin folder names contain spaces. Use `python3` on macOS; the SDK's own commands say `python`, which may not exist there (`AGENTS.md`). All tools are Python 3.9+ scripts that use only the standard library.

Checked against the SDK at commit `e78bad5`. Each section names the file whose usage text and argument parser it comes from.

## Build: `tools/build.py`

```bash
python3 "<sdk>/tools/build.py" "<project>" [--target all|arm32|arm64|native|desktop] \
    [--toolchain zig|gcc|docker] [--zig PATH] [--no-ui] [--no-validate] [--debug] \
    [--define NAME=VALUE] [--verbose]
```

- The project is the one positional argument. There is no `--dir` and no output option: output always goes into `<project>/build/`.
- `--target all` (the default) builds, in order: the native library, a parameter dump, the 32-bit and 64-bit ARM libraries, the finished plugin folder, `version.xml`, and then runs the validation tool on it. `--target native` stops after the native library and parameter dump.
- Output:
  - `<project>/build/native/<slug>.dylib` on macOS (`.so` on Linux, `.dll` on Windows): the native build, for the host simulator
  - `<project>/build/params.json`: what the binary reports, from `host_sim dump`
  - `<project>/build/<Manufacturer> - VST - <Name>/`: the finished plugin folder, with `plugin.json`, `version.xml`, `VST/<slug>-arm32.so`, `VST/<slug>-arm64.so`, `Plugin Skins/` (unless `--no-ui` and no `skins/` folder) and `Content/` (copied from the project's `Content/`, if it has one)
- `<slug>` is the plugin's `name` from `plugin.json`, lower-cased, with every character other than `a-z` and `0-9` replaced by `-`.
- The compiler gets `-I <sdk>/framework` and `-I <project>/src`, so the project includes the framework headers (`mpc_plugin.h` and the rest) without copying them. It compiles only `<project>/src/*.cpp`.
- zig, under the default `--toolchain zig`, is looked up in this order: `--zig`, `$ZIG`, `zig` on `PATH`, then a private environment in `<sdk>/.sdk-tools/zigenv`. `--zig` and `$ZIG` accept a zig executable or a Python interpreter that has the `ziglang` package.
- The build compiles the host simulator into `<sdk>/.sdk-tools/host_sim` when it is missing or older than its source (`tools/host-sim/host_sim.cpp`) or the framework's VST2 interface header (`framework/mpc_vst2_abi.h`). These are the builds that write into the SDK: see [sdk-edge-cases.md](sdk-edge-cases.md).
- Exit codes: 0 success, 1 compile failure, validation errors or missing project, 2 bad arguments.
- Its closing "Next:" hint prints the packaging command with an SDK-relative path (`tools/package.py`); make it absolute before running it.

Source: `tools/build.py` (module docstring, `parse_args`, `main`, `Builder.common_flags`, `find_zig`, `ensure_host_sim`, `make_slug`).

## Validation: `tools/validate.py`

```bash
python3 "<sdk>/tools/validate.py" "<project>" [--strict]
python3 "<sdk>/tools/validate.py" "<project>/build/<Manufacturer> - VST - <Name>" [--params "<project>/build/params.json"] [--strict]
```

- Takes either the project folder (it then uses `<project>/build/<folder>` and `<project>/build/params.json`) or the built plugin folder.
- Checks the manifest, the folder name, each ARM library (architecture, linked libraries, glibc versions, the exported entry point), that `params.json` agrees with `plugin.json`, the MPC Sample Knob FX mapping (printed as knob → parameter lines), the skins and `version.xml`.
- Prints `OK`, `WARN` and `ERROR` lines. Exit 1 on any `ERROR`, or on any `WARN` with `--strict`; otherwise 0.
- The build runs it already; run it alone after changing the output folder or to see the Knob FX mapping again.

Source: `tools/validate.py` (module docstring, `main`, `validate`).

## Packaging: `tools/package.py`

```bash
python3 "<sdk>/tools/package.py" "<project>" [--out "<folder>"]
```

- Needs a finished build in `<project>/build/`.
- Writes `<project>/dist/<slug>-<version>-mpc.zip` (or into `--out`), holding the plugin folder at the top level, an `INSTALL.txt`, and the project's `README.md` if there is one.

Source: `tools/package.py` (module docstring, `main`).

## Scaffolding: `tools/new_plugin.py`

```bash
python3 "<sdk>/tools/new_plugin.py" "<Name>" --vendor "<Manufacturer>" [--kind instrument|effect] --dir "<parent folder>"
```

- Creates `<parent folder>/<Name>/` from the SDK's template for that kind, and refuses to overwrite an existing folder. `--kind` defaults to `instrument`.
- `--dir` is the **parent** folder, not the project folder. Its default is `<sdk>/plugins`, so leaving it out puts the project inside the SDK.
- Only for a new project the user asked for. An existing project is never re-scaffolded.

Source: `tools/new_plugin.py` (module docstring, `main`).

## Host simulator: `<sdk>/.sdk-tools/host_sim`

```bash
"<sdk>/.sdk-tools/host_sim" "<project>/build/native/<slug>.dylib" test [--seconds N] [--sr N] [--block N] \
    [--wav "<project>/build/test.wav"] [--notes 60,64,67] [--playing] [--seed N] [--verbose]
"<sdk>/.sdk-tools/host_sim" "<project>/build/native/<slug>.dylib" dump
```

- A small VST2 host that behaves like the MPC's: it loads the **native** build (not the ARM libraries), runs the MPC's load sequence, renders audio, and prints `PASS`, `WARN`, `FAIL` and `INFO` lines, then a `Result:` line. `dump` prints the parameter list as JSON.
- Exit codes: 0 pass (warnings allowed), 1 at least one `FAIL` or bad arguments, 2 the plugin crashed (the report names the phase and the last call).
- A `FAIL` means the MPC would reject the plugin, crash or produce broken audio. Treat any `FAIL` as a failed check. A `WARN` may be intentional, but say what it is.
- It lives in the SDK's tool cache, not in the project. On Windows it is `host_sim.exe`.

Source: `tools/host-sim/README.md` ("Commands", "Reading the report"), `tools/host-sim/host_sim.cpp` (`usage`, the `Result:` line), `tools/build.py` (`host_sim_path`).

## What lives where

| Path | Written by | Notes |
|---|---|---|
| `<project>/build/` | build | native library, `params.json`, the finished plugin folder |
| `<project>/dist/` | packaging | the zip to share |
| `<sdk>/.sdk-tools/host_sim` | build | the host simulator |
| `<sdk>/.sdk-tools/zigenv/` | build | zig, when the build installs it |

The SDK's own `.gitignore` ignores `build/`, `dist/` and `.sdk-tools/`. Nothing else moves between the two folders: SDK files are never copied into the project, and the project is never moved or copied into the SDK.
