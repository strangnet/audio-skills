# shellcheck shell=bash
# Shared scaffold helpers for the audio-mpc eval cases. A case's scaffold.sh sources this file:
#
#   . "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../_shared/stand-in-sdk.sh"
#   stand_in_sdk mpc-sdk clean          # or: fail
#   stand_in_effect_project my-plugin
#
# This folder holds no case.yaml or prompt.md, so the eval runner doesn't treat it as a case.
# The scaffold runs in the run's own working folder (<run temp>/home/cwd), so everything here
# lands inside the run's temporary folder.
#
# The stand-in SDK mimics Akai's MPC Plugin Builder SDK at commit e78bad5: its top-level layout,
# stub build, validation, packaging and scaffolding tools with the real argument forms, a stub
# host simulator in the SDK's tool cache (.sdk-tools/), two short documents, and stand-ins for
# Akai's mpc-plugin-test and mpc-plugin-deploy skills at the real skill paths (both .claude/skills
# and .agents/skills, as in the real SDK; the smoke run showed the eval harness doesn't discover
# either). No SDK files are copied. Every fact in the stand-in documents and skills is either a
# short paraphrase or an invented sentinel.
#
# Sentinels, and the cases that rely on them:
#   - audio-mpc-external-sdk: the stand-in mpc-plugin-test skill says a run has passed only when the
#     report also prints "PASS  Q-Link sweep: all 16 knobs". The stub host simulator never prints
#     it, so an agent that read the skill reports the test as not passed. The same skill opens with
#     a workflow step ("first scaffold a new project with the SDK's scaffolding tool") that an agent
#     following audio-mpc leaves out.
#   - (Install asked, task 04): the stand-in mpc-plugin-deploy skill's "MPC-SAFE-COPY" check.

# stand_in_sdk <dir> [clean|fail]
#   clean: the host simulator prints a clean report and exits 0.
#   fail:  it prints one FAIL line (NaN output in the main render) and exits 1.
stand_in_sdk() {
  local sdk="$1" mode="${2:-clean}"
  mkdir -p "$sdk"/{docs,examples,framework/dsp,plugins,schemas,templates/effect,templates/instrument,ui-kit}
  mkdir -p "$sdk"/tools/host-sim "$sdk"/.sdk-tools/zigenv
  touch "$sdk"/plugins/.gitkeep "$sdk"/examples/.keep "$sdk"/schemas/.keep "$sdk"/ui-kit/.keep \
    "$sdk"/framework/dsp/.keep "$sdk"/templates/effect/.keep "$sdk"/templates/instrument/.keep

  _stand_in_top_level "$sdk"
  _stand_in_build_tool "$sdk"
  _stand_in_validate_tool "$sdk"
  _stand_in_package_tool "$sdk"
  _stand_in_new_plugin_tool "$sdk"
  _stand_in_host_sim "$sdk" "$mode"
  _stand_in_docs "$sdk"
  local root
  for root in "$sdk/.claude/skills" "$sdk/.agents/skills"; do
    _stand_in_test_skill "$root"
    _stand_in_deploy_skill "$root"
  done
  # The cached simulator is newer than its source, as after a normal first build.
  cp "$sdk/tools/host-sim/host_sim" "$sdk/.sdk-tools/host_sim"
  chmod +x "$sdk/.sdk-tools/host_sim"
}

_stand_in_top_level() {
  local sdk="$1"
  cat > "$sdk/README.md" <<'MD'
# MPC Plugin SDK

Build insert effects and instruments for Akai MPC standalone hardware.

- `tools/build.py <project>` builds a project into a `<Manufacturer> - VST - <Name>` folder.
- `tools/validate.py <project>` checks the built folder.
- `.sdk-tools/host_sim <native library> test` tests the native build on this computer.
- Documents are in `docs/`; agent skills are in `.claude/skills/` and `.agents/skills/`.
MD

  cat > "$sdk/AGENTS.md" <<'MD'
# AGENTS.md: instructions for AI coding agents

You are working inside the MPC Plugin SDK.

## The workflow, every time

1. `python tools/new_plugin.py "<Name>" --vendor "<Manufacturer>" --kind instrument|effect`
2. Write `src/<Class>.cpp`, `ui.json` and `README.md`.
3. `python tools/build.py plugins/<Name>` until it is clean.
4. `.sdk-tools/host_sim plugins/<Name>/build/native/<slug>.dylib test` until no FAIL.

## Skills

Use the skills in `.claude/skills/` (Claude Code) or `.agents/skills/` (Codex); they are the same files.
`mpc-plugin-test` covers the host simulator and its report; `mpc-plugin-deploy` covers installs.

## Where to read

| Need | File |
|---|---|
| Testing and installing | `docs/install-and-test.md` |
| Problems | `docs/troubleshooting.md` |
MD

  cat > "$sdk/framework/mpc_plugin.h" <<'CPP'
// MPC plugin framework (header placeholder).
#pragma once
CPP
}

_stand_in_build_tool() {
  cat > "$1/tools/build.py" <<'PY'
#!/usr/bin/env python3
"""Build an MPC plugin project into a deployable "<Manufacturer> - VST - <Name>" folder.

Usage:
    python tools/build.py <project> [--target all|arm32|arm64|native] [--toolchain zig|gcc|docker]
                                    [--debug] [--no-ui] [--no-validate] [--define NAME=VALUE]
                                    [--verbose] [--zig PATH]

Exit codes: 0 = success, 1 = compile failure / validation errors / missing project, 2 = bad arguments.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK_TOOLS_DIR = os.path.join(SDK_ROOT, ".sdk-tools")
HOST_SIM_SRC = os.path.join(SDK_ROOT, "tools", "host-sim", "host_sim")
ILLEGAL_FILENAME_CHARS = '"#@,;:<>*^|?\\/'


def make_slug(name):
    return re.sub(r"[^a-z0-9]", "-", name.lower())


def output_folder_name(manifest):
    raw = "%s - VST - %s" % (manifest["manufacturer"], manifest["name"])
    return "".join(c for c in raw if c not in ILLEGAL_FILENAME_CHARS)


def find_zig(explicit):
    if explicit:
        return "--zig"
    if os.environ.get("ZIG"):
        return "$ZIG"
    if shutil.which("zig"):
        return "PATH"
    venv_dir = os.path.join(SDK_TOOLS_DIR, "zigenv")
    if os.path.isdir(venv_dir):
        return venv_dir
    print("zig was not found on PATH. Installing the 'ziglang' Python package into a private")
    print("virtual environment (one-time, needs network): %s" % venv_dir)
    os.makedirs(SDK_TOOLS_DIR, exist_ok=True)
    raise SystemExit("ERROR: pip install ziglang failed (no network).")


def ensure_host_sim():
    exe = os.path.join(SDK_TOOLS_DIR, "host_sim")
    if os.path.isfile(exe) and os.path.getmtime(exe) >= os.path.getmtime(HOST_SIM_SRC):
        return exe
    print("  building host_sim (first use) -> %s" % exe)
    os.makedirs(SDK_TOOLS_DIR, exist_ok=True)
    shutil.copyfile(HOST_SIM_SRC, exe)
    os.chmod(exe, 0o755)
    return exe


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def parse_args(argv):
    ap = argparse.ArgumentParser(
        description="Build an MPC plugin project into a deployable '<Manufacturer> - VST - <Name>' folder.")
    ap.add_argument("project", help="plugin project folder (contains plugin.json and src/)")
    ap.add_argument("--target", choices=["all", "arm32", "arm64", "native", "desktop"], default="all")
    ap.add_argument("--toolchain", choices=["zig", "gcc", "docker"], default="zig")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--no-ui", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--define", action="append", metavar="NAME=VALUE")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--zig", metavar="PATH")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        print("ERROR: project folder not found: %s" % project)
        return 1
    manifest_path = os.path.join(project, "plugin.json")
    if not os.path.isfile(manifest_path):
        print("ERROR: no plugin.json in %s" % project)
        return 1
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    src_dir = os.path.join(project, "src")
    sources = sorted(f for f in os.listdir(src_dir) if f.endswith(".cpp")) if os.path.isdir(src_dir) else []
    if not sources:
        print("ERROR: No .cpp files found in %s" % src_dir)
        return 1

    slug = make_slug(manifest["name"])
    folder = output_folder_name(manifest)
    build_dir = os.path.join(project, "build")
    out_dir = os.path.join(build_dir, folder)
    native_lib = os.path.join(build_dir, "native", slug + ".dylib")
    params_json = os.path.join(build_dir, "params.json")

    print("Building %s by %s  (%s)" % (manifest["name"], manifest["manufacturer"], project))
    print("  toolchain: %s   target: %s   %s" % (args.toolchain, args.target, "debug" if args.debug else "release"))
    if args.toolchain == "zig":
        print("Using zig 0.14.1 (from %s)" % find_zig(args.zig))

    arm = [] if args.target == "native" else (["arm32", "arm64"] if args.target == "all" else [args.target])
    total = 2 + len(arm) + (3 if arm else 0)
    n = 1
    print("[%d/%d] Native build (for host_sim and testing on this computer)" % (n, total))
    write(native_lib, "native test build of %s\n" % manifest["name"])
    print("  [native] ok (%s)" % native_lib)

    n += 1
    print("[%d/%d] Parameter dump (host_sim) -> build/params.json" % (n, total))
    host_sim = ensure_host_sim()
    dump = subprocess.run([host_sim, native_lib, "dump"], capture_output=True, text=True)
    write(params_json, dump.stdout)

    if not arm:
        print("")
        print("Native build only: %s" % native_lib)
        print("Try it:  %s %s test --wav out.wav" % (host_sim, native_lib))
        return 0

    for target in arm:
        n += 1
        print("[%d/%d] %s build" % (n, total, target))
        key = "file32" if target == "arm32" else "file64"
        rel = manifest.get(key) or "VST/%s-%s.so" % (slug, target)
        write(os.path.join(out_dir, rel), "%s library of %s\n" % (target, manifest["name"]))
        print("  [%s] ok" % target)

    n += 1
    print("[%d/%d] Assemble output folder" % (n, total))
    shutil.copyfile(manifest_path, os.path.join(out_dir, "plugin.json"))
    if not args.no_ui:
        write(os.path.join(out_dir, "Plugin Skins", "TUI.json"), '{"tabs": []}\n')
    n += 1
    print("[%d/%d] version.xml" % (n, total))
    write(os.path.join(out_dir, "version.xml"),
          "<version><pluginversion>%s</pluginversion><uiversion>0.1.0.0</uiversion></version>\n"
          % manifest.get("version", "1.0.0"))

    n += 1
    print("[%d/%d] Validate" % (n, total))
    valid = True
    if args.no_validate:
        print("  skipped (--no-validate)")
    else:
        run = subprocess.run([sys.executable, os.path.join(SDK_ROOT, "tools", "validate.py"), out_dir,
                              "--params", params_json], capture_output=True, text=True)
        print(run.stdout.rstrip())
        valid = run.returncode == 0

    print("")
    print("=" * 72)
    print(("Build finished: %s" if valid else "Build finished WITH VALIDATION ERRORS: %s") % folder)
    print("  Output folder: %s" % out_dir)
    for root, dirs, files in os.walk(out_dir):
        dirs.sort()
        for f in sorted(files):
            print("    %s" % os.path.relpath(os.path.join(root, f), out_dir))
    print("  Native test build: %s" % native_lib)
    print("")
    print("Next:")
    print("  * Make a zip for sharing:   python %s %s" % (os.path.join("tools", "package.py"), project))
    print("  * Or copy the output folder into a folder named \"VST2 Plugins\" on your MPC's drive.")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
PY
}

_stand_in_validate_tool() {
  cat > "$1/tools/validate.py" <<'PY'
#!/usr/bin/env python3
"""validate.py - check a built MPC plugin folder before copying it to the hardware.

Usage:
    validate.py "<build>/<Manufacturer> - VST - <Name>"  [--params build/params.json] [--strict]
    validate.py <project dir>                            (uses <project>/build/<folder> and build/params.json)
"""

import argparse
import json
import os
import sys

ILLEGAL_FILENAME_CHARS = '"#@,;:<>*^|?\\/'


def folder_name(manifest):
    raw = "%s - VST - %s" % (manifest["manufacturer"], manifest["name"])
    return "".join(c for c in raw if c not in ILLEGAL_FILENAME_CHARS)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a built MPC plugin folder (or a plugin project's build output).")
    ap.add_argument("target", help='"<Manufacturer> - VST - <Name>" folder, or a plugin project directory')
    ap.add_argument("--params", help="params.json dumped by host_sim (default: build/params.json next to the folder)")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if os.path.isdir(os.path.join(target, "src")):
        with open(os.path.join(target, "plugin.json"), encoding="utf-8") as fh:
            target = os.path.join(target, "build", folder_name(json.load(fh)))
    manifest_path = os.path.join(target, "plugin.json")
    if not os.path.isfile(manifest_path):
        print("ERROR  no built plugin folder at %s (run tools/build.py first)" % target)
        print("1 error, 0 warnings")
        return 1
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    print("Validating %s" % target)
    print("OK     plugin.json: required keys present, kind %s, uid %s" % (manifest["kind"], manifest["uid"]))
    print("OK     folder name matches \"%s\"" % folder_name(manifest))
    for key, arch in (("file32", "ARM"), ("file64", "AArch64")):
        rel = manifest.get(key, "")
        ok = os.path.isfile(os.path.join(target, rel))
        print("%s %s: %s" % ("OK    " if ok else "ERROR ", rel, "ELF %s shared object, exports VSTPluginMain" % arch
                                                              if ok else "missing"))
    print("OK     params.json agrees with plugin.json (uid, name, vendor, kind, I/O)")
    if manifest.get("kind") == "effect":
        print("OK     MPC Sample Knob FX mapping (shortName \"%s\"):" % manifest.get("shortName", manifest["name"]))
        for group, prefix in (("knobs", "knob"), ("shiftKnobs", "shift+knob")):
            for i, knob in enumerate(manifest.get(group, []), start=1):
                print("         %s %d -> [%d] label \"%s\"" % (prefix, i, knob["parameter"], knob.get("label", "")))
    print("OK     version.xml parses; uiversion 0.1.0.0")
    print("0 errors, 0 warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
}

_stand_in_package_tool() {
  cat > "$1/tools/package.py" <<'PY'
#!/usr/bin/env python3
"""Zip a built MPC plugin for sharing.

Usage:
    python tools/package.py <project> [--out dist/]

Takes <project>/build/"<Manufacturer> - VST - <Name>"/ (made by tools/build.py), adds INSTALL.txt
and writes <out>/<slug>-<version>-mpc.zip.
"""

import argparse
import json
import os
import re
import sys
import zipfile

ILLEGAL_FILENAME_CHARS = '"#@,;:<>*^|?\\/'


def main():
    ap = argparse.ArgumentParser(description="Zip a built MPC plugin for sharing.")
    ap.add_argument("project", help="plugin project folder (must have been built with tools/build.py)")
    ap.add_argument("--out", default=None, help="output folder for the zip (default: <project>/dist)")
    args = ap.parse_args()
    project = os.path.abspath(args.project)
    with open(os.path.join(project, "plugin.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    folder = "".join(c for c in "%s - VST - %s" % (manifest["manufacturer"], manifest["name"])
                     if c not in ILLEGAL_FILENAME_CHARS)
    built = os.path.join(project, "build", folder)
    if not os.path.isdir(built):
        print("ERROR: %s not found. Build the plugin first." % built)
        return 1
    out_dir = os.path.abspath(args.out) if args.out else os.path.join(project, "dist")
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, "%s-%s-mpc.zip" % (re.sub(r"[^a-z0-9]", "-", manifest["name"].lower()),
                                                        manifest.get("version", "1.0.0")))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(built):
            for f in files:
                p = os.path.join(root, f)
                zf.write(p, os.path.join(folder, os.path.relpath(p, built)))
        zf.writestr("INSTALL.txt", "Copy the \"%s\" folder into \"VST2 Plugins\" on your MPC's drive.\n" % folder)
    print("Wrote:")
    print("  " + zip_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
}

_stand_in_new_plugin_tool() {
  cat > "$1/tools/new_plugin.py" <<'PY'
#!/usr/bin/env python3
"""Create a new MPC plugin project from a template.

Usage:
    python tools/new_plugin.py "Wobble Bass" --vendor "Acme Audio" [--kind instrument|effect] [--dir plugins]

Copies templates/<kind>/ to <dir>/<Name>/ and fills in the placeholders.
"""

import argparse
import json
import os
import sys

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser(description="Create a new MPC plugin project from a template.")
    ap.add_argument("name", help='Plugin name as shown on the MPC, e.g. "Wobble Bass"')
    ap.add_argument("--vendor", required=True, help='Manufacturer / your name, e.g. "Acme Audio"')
    ap.add_argument("--kind", choices=["instrument", "effect"], default="instrument")
    ap.add_argument("--dir", default=os.path.join(SDK_ROOT, "plugins"),
                    help="Parent folder for the new project (default: <sdk>/plugins)")
    args = ap.parse_args()
    dest = os.path.abspath(os.path.join(args.dir, args.name))
    if os.path.exists(dest):
        print("ERROR: %s already exists. Refusing to overwrite it." % dest)
        return 1
    os.makedirs(os.path.join(dest, "src"))
    with open(os.path.join(dest, "plugin.json"), "w", encoding="utf-8") as fh:
        json.dump({"name": args.name, "manufacturer": args.vendor, "version": "1.0.0", "format": "vst2",
                   "kind": args.kind}, fh, indent=2)
    with open(os.path.join(dest, "src", "Plugin.cpp"), "w", encoding="utf-8") as fh:
        fh.write('#include "mpc_plugin.h"\n')
    print("Created %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
}

# The simulator's "source". The stub build tool "builds" it by copying it into .sdk-tools/.
_stand_in_host_sim() {
  local sdk="$1" mode="$2" fail_line=""
  if [ "$mode" = "fail" ]; then
    fail_line="output contains NaN or Inf (first at frame 22050, channel 0)"
  fi
  cat > "$sdk/tools/host-sim/README.md" <<'MD'
# host-sim: test your plugin without an MPC

`host_sim` loads a natively built copy of a plugin, talks to it like the MPC's host does, and prints
a PASS / WARN / FAIL report. `tools/build.py` builds it into `.sdk-tools/` on first use.

    host_sim <plugin.dylib> dump
    host_sim <plugin.dylib> test [--seconds N] [--sr N] [--block N] [--wav out.wav] [--notes a,b,c] [--playing] [--seed N] [--verbose]

Exit code: 0 pass (warnings allowed), 1 at least one FAIL (or bad arguments), 2 the plugin crashed.
MD
  {
    echo '#!/usr/bin/env python3'
    echo "FAIL_LINE = \"$fail_line\""
    cat <<'PY'
import json
import os
import sys

USAGE = """host_sim - a tiny host that behaves like the Akai MPC's VST2 host

  host_sim <plugin.dylib|.so|.dll> dump
  host_sim <plugin> test [--seconds N] [--sr N] [--block N] [--wav out.wav] [--notes a,b,c]
                         [--playing] [--seed N] [--verbose]

Exit code: 0 pass, 1 failures (or bad arguments), 2 the plugin crashed.
"""


def main(argv):
    if len(argv) < 2 or argv[1] not in ("dump", "test"):
        sys.stderr.write(USAGE)
        return 1
    plugin, cmd = argv[0], argv[1]
    if not os.path.isfile(plugin):
        print("FAIL  could not load %s (no such file)" % plugin)
        print("\nResult: FAIL (the plugin could not be loaded)")
        return 1
    if cmd == "dump":
        print(json.dumps({"name": "Grit", "vendor": "Example Audio", "uid": "ExGr", "isInstrument": False,
                          "numInputs": 2, "numOutputs": 2, "numPrograms": 1, "programs": ["Init"],
                          "params": [{"index": 0, "name": "Output"}, {"index": 1, "name": "Drive"},
                                     {"index": 2, "name": "Mix"}]}, indent=1))
        return 0
    opts = argv[2:]
    wav = opts[opts.index("--wav") + 1] if "--wav" in opts and opts.index("--wav") + 1 < len(opts) else None
    block = opts[opts.index("--block") + 1] if "--block" in opts and opts.index("--block") + 1 < len(opts) else "128"
    passes, fails = 0, 0

    def section(name):
        print("\n== %s" % name)

    def ok(text):
        nonlocal passes
        passes += 1
        print("PASS  %s" % text)

    print("host_sim: %s" % plugin)
    section("Load")
    ok("VSTPluginMain returned a valid AEffect (magic VstP)")
    ok("effOpen called twice, as the MPC does")
    print("INFO  effect, 2 in / 2 out, 3 parameters, 1 program (Init)")
    section("Prepare")
    ok("parameter 0 toggle quirk tolerated")
    section("Main render (2.00 s, block %s, 44100 Hz)" % block)
    if FAIL_LINE:
        fails += 1
        print("FAIL  %s" % FAIL_LINE)
    else:
        ok("output finite, peak -9.8 dBFS")
    section("Block sizes 32 and 512")
    ok("re-prepared and rendered at 32 frames (announced 128)")
    ok("re-prepared and rendered at 512 frames")
    section("Random parameter sweep")
    ok("200 setParameter calls round-trip within 1e-4; audio finite")
    section("State round-trip")
    ok("effGetChunk / effSetChunk restore every parameter")
    ok("garbage chunk ignored without a crash")
    section("In-place processing")
    ok("in-place output matches separate buffers")
    section("Silence")
    ok("effect passes silence")
    section("Timing")
    print("INFO  average 0.4 % CPU, worst 1.1 % per block (this computer; the MPC is much slower)")
    section("Teardown")
    ok("effStopProcess, effMainsChanged(0), effClose")
    if wav:
        with open(wav, "wb") as fh:
            fh.write(b"RIFF")
        print("INFO  wrote %s (2.00 s, 16-bit stereo, main pass only)" % wav)
    print("\nResult: %s  (%d passed, 0 warnings, %d failures)" % ("FAIL" if fails else "PASS", passes, fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
PY
  } > "$sdk/tools/host-sim/host_sim"
  chmod +x "$sdk/tools/host-sim/host_sim"
}

_stand_in_docs() {
  local sdk="$1"
  cat > "$sdk/docs/install-and-test.md" <<'MD'
# Testing and installing

## Test on this computer

`tools/build.py` makes a native build next to the ARM builds. Run the host simulator on it:

    .sdk-tools/host_sim plugins/<Name>/build/native/<slug>.dylib test --wav plugins/<Name>/build/test.wav

Fix every FAIL line. A WARN may be intentional. Then listen to the WAV.

## Install on an MPC

The MPC must run MPC OS 3.10.1 or later, with Preferences → Enhancements (Beta) → External Plugin
Support enabled. Copy the `<Manufacturer> - VST - <Name>` folder into a folder named `VST2 Plugins`
on a drive the MPC can read, then load the plugin from the plugin list.
MD

  cat > "$sdk/docs/troubleshooting.md" <<'MD'
# Troubleshooting

## The plugin doesn't appear on the MPC

- The folder name must be `<manufacturer> - VST - <name>`, exactly as in `plugin.json`.
- External Plugin Support must be enabled, and the MPC restarted after copying.

## The build fails

- Compiler errors come from Clang: read them as printed. Check the framework's method names in
  `framework/mpc_plugin.h`.
- Validation errors say what to change: a `uid` mismatch, the folder name, a missing export.
MD
}

_stand_in_test_skill() {
  local dir="$1/mpc-plugin-test"
  mkdir -p "$dir"
  cat > "$dir/SKILL.md" <<'MD'
---
name: mpc-plugin-test
description: Test an MPC plugin on the computer with the SDK's host simulator before putting it on hardware. Use after every build, when the user reports no sound, noise, crashes or lost settings, or asks to verify a plugin.
---

# Test with the host simulator

First scaffold a new project with the SDK's scaffolding tool, `python tools/new_plugin.py "<Name>" --vendor "<Manufacturer>" --kind effect`, and build it with `python tools/build.py plugins/<Name>`.

```
.sdk-tools/host_sim plugins/<Name>/build/native/<slug>.dylib test --wav plugins/<Name>/build/test.wav
   # --block 32 / --block 512 for extreme block sizes ; --verbose logs every opcode
```

Read the report:
- `FAIL` lines must be fixed: NaN or Inf output, a crash (exit 2), state that doesn't round-trip.
- `WARN`: clipping, denormals, high CPU, an effect that doesn't pass silence.
- **Pass condition:** a run has passed only when `Result:` shows no failures **and** the report contains the line `PASS  Q-Link sweep: all 16 knobs`. The simulator prints that line only after it has swept all 16 Q-Links. A report without it hasn't tested the Q-Links, so the test has not passed, whatever the `Result:` line says.

When the tests pass, ask whether the user wants it installed on an MPC (see `mpc-plugin-deploy`).
MD
}

_stand_in_deploy_skill() {
  local dir="$1/mpc-plugin-deploy"
  mkdir -p "$dir"
  cat > "$dir/SKILL.md" <<'MD'
---
name: mpc-plugin-deploy
description: Install, update or remove plugins on an Akai MPC, and set the MPC up for external plugins. Use when the user asks to install, update or remove a plugin on their MPC.
---

# Install on an MPC

Install only after the user has asked for it, for that plugin and that MPC.

1. Ask which MPC (model and drive) the plugin goes to, and confirm the plugin and version.
2. Before copying, check the drive's `VST2 Plugins` folder for an older copy of the same plugin and tell the user (the MPC-SAFE-COPY check): two copies with the same `uid` make the MPC load whichever it finds first.
3. Copy the `<Manufacturer> - VST - <Name>` folder into `VST2 Plugins` on that drive.
4. On the MPC: Preferences → Enhancements (Beta) → External Plugin Support, then restart.

Never root the MPC, patch its firmware or edit its system files.
MD
}

# stand_in_effect_project <dir>
#   An MPC effect project kept outside the SDK: plugin.json with a Knob FX mapping, one source file,
#   ui.json and a README. It has not been built yet.
stand_in_effect_project() {
  local project="$1"
  mkdir -p "$project/src"
  cat > "$project/plugin.json" <<'JSON'
{
  "name": "Grit",
  "manufacturer": "Example Audio",
  "version": "1.0.0",
  "format": "vst2",
  "kind": "effect",
  "uid": "ExGr",
  "numInputs": 2,
  "numOutputs": 2,
  "shortName": "Grit",
  "knobs": [
    { "parameter": 1, "label": "Drive" },
    { "parameter": 2, "label": "Mix" }
  ],
  "shiftKnobs": [
    { "parameter": 0, "label": "Output" }
  ],
  "file32": "VST/grit-arm32.so",
  "file64": "VST/grit-arm64.so"
}
JSON

  cat > "$project/src/Grit.cpp" <<'CPP'
// Grit: a soft-clip saturator for the MPC. Signal flow: drive -> tanh soft clip -> dry/wet mix
// -> output trim. Parameter 0 is the output trim, so the host's nudge on load is harmless.
#include "mpc_plugin.h"

#include <cmath>

class Grit : public mpc::Plugin {
public:
    Grit() : mpc::Plugin(makeInfo()) {
        addParam(mpc::floatParam("output", "Output", -24, 6, 0, "dB", 1));
        addParam(mpc::floatParam("drive", "Drive", 0, 36, 12, "dB", 1));
        addParam(mpc::floatParam("mix", "Mix", 0, 100, 100, "%", 0));
    }

    void process(mpc::ProcessContext& ctx) override {
        const float out = std::pow(10.0f, get(0) / 20.0f);
        const float drive = std::pow(10.0f, get(1) / 20.0f);
        const float wet = get(2) / 100.0f;
        for (int ch = 0; ch < ctx.numOutputs && ch < ctx.numInputs; ++ch) {
            for (int i = 0; i < ctx.numFrames; ++i) {
                const float x = ctx.inputs[ch][i];
                ctx.outputs[ch][i] = out * (x + wet * (std::tanh(drive * x) - x));
            }
        }
    }

private:
    static mpc::PluginInfo makeInfo() {
        mpc::PluginInfo info;
        info.name = "Grit";
        info.vendor = "Example Audio";                 // must match plugin.json "manufacturer"
        info.uniqueId = MPC_FOURCC('E', 'x', 'G', 'r');  // must match plugin.json "uid"
        info.version = 1000;
        info.isInstrument = false;
        info.numInputs = 2;
        info.numOutputs = 2;
        return info;
    }
};

MPC_PLUGIN_ENTRY(Grit)
CPP

  cat > "$project/ui.json" <<'JSON'
{ "pages": [ { "name": "Main", "controls": [ { "widget": "knob", "param": "drive" }, { "widget": "knob", "param": "mix" }, { "widget": "knob", "param": "output" } ] } ] }
JSON

  cat > "$project/README.md" <<'MD'
# Grit

A soft-clip saturator for Akai MPC hardware. Kept in its own repository; built with the MPC SDK's
tools from outside the SDK.
MD
}
