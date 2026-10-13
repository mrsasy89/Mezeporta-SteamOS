# SteamOS handoff — 2026-10-09

> Historical checkpoint. For the current verified AppImage, native 1080p Gaming
> Mode, required Steam Linux Runtime and build instructions, read
> [SteamOS.md](SteamOS.md), [Windows.md](Windows.md) and the main README.
> The startup/game-launch status below describes 9 October, not the current port.

## Goal and current status

Port Mezeporta CLI-dev to SteamOS, initially Desktop Mode, for an Erupe
server upgraded from 9.2.1 to 9.6.1. The previous MHFZ-Launcher works with
Proton Experimental and is the implementation reference. Keep the
meze-deps interface until evidence supports changing it. Gaming Mode and
packaging follow successful Desktop login, launch and exit.

**The launcher builds and stays open with `--no-watch`. Proton executes on
the host. Game launch has NOT succeeded. This commit is a diagnostic
checkpoint, not a working SteamOS port.**

Work step by step, inspect the real files and record evidence for each
change. Commit verified milestones to the maintainer's fork. Do not
publish passwords, tokens, runtime config, game files, prefixes or logs.

## Sources and baseline

- Fork: https://github.com/mrsasy89/Mezeporta
- Upstream: https://github.com/LilButter/Mezeporta
- Starting branch: CLI-dev
- Pinned commit: `0d7712f99700ff643c834cc3fd668a4767ca5a05`
- Reference: https://github.com/mrsasy89/MHFZ-Launcher
  - Inspected commit: `1df702fbf6f08a764c249fdf855874a7a650f807`
  - Host dispatch: `src-tauri/src/lib_linux.rs`
- Related repositories, not fully audited:
  - https://github.com/mrsasy89/mhf-iel
  - https://github.com/LilButter/Mezeporta-Wrapper
  - https://github.com/mrsasy89/Erupe
  - https://github.com/Houmgaor/Erupe
  - https://github.com/mrsasy89/MHFZ-Patch-Server

## Maintainer's actual environment

- Host: SteamOS, user `deck`, hostname `steammachine`, Desktop Mode.
- Container: Arch Distrobox named `mhfz-dev`.
- Checkout: `/home/deck/Progetti/Mezeporta-steamos`, local `steamos-dev`.
- Game currently selected: `/home/deck/Applications/MH Frontier Z`.
- A second directory `/home/deck/Applications/MH-Frontier-Z` also exists.
  Do not silently switch between the two.
- Host execution command available: `/usr/bin/distrobox-host-exec`.
- Host Python: `/usr/bin/python3`.
- Experimental script:
  `/home/deck/.local/share/Steam/steamapps/common/Proton - Experimental/proton`.
- Other installed Proton names: 10.0, 11.0, Hotfix.
- Search also returns paths under `~/.steam/steam`; check symlinks before
  treating them as separate installations.
- Current compat-data root: `<game>/Mezeporta/ProtonData`.

These are observed local paths, not defaults to hard-code into the port.

## Verified launcher build and development issue

The Arch dependency verifier passed. `npm ci` and the Rust build succeeded.
Incompatible manual dependency upgrades (Vite 4 to 8, Tailwind 3 to 4,
DaisyUI 3 to 5) caused frontend errors; the maintainer restored package.json
and package-lock.json and ran npm ci again. Baseline lock versions include
Vite 4.5.14, Tailwind 3.3.5 and plugin-vue 4.4.1. Do not run audit fix --force.
The installation still reports vulnerabilities and blocked install scripts
for esbuild/vue-demi. Handle dependency maintenance separately.

Cargo updated the local meze-butter package version in Cargo.lock from
1.5.2 to 1.5.4 during compilation. Inspect the actual diff before committing.

The app writes config and WebView localstorage into src-tauri/Mezeporta.
Tauri watches those writes and repeatedly rebuilds/restarts the app.
`--no-watch` prevents the loop. The permanent watcher exclusion is not
implemented in this checkpoint. `.gitignore` alone is NOT verified to fix it.
GTK module warnings and WebKit errors were observed during the restart loop;
they have not been demonstrated to be the game-launch cause.

## Relevant code findings

Inspect src-tauri/src/main.rs, src-tauri/src/cli.rs and
src-tauri/meze-butter/src/{lib.rs,mhf.rs,bin/meze_deps.rs}.

- The old launcher dispatches Proton to the host using distrobox-host-exec.
  Mezeporta launches runtime commands directly inside the container,
  including preparation/registry/font operations.
- resolve_proton_command supports MEZEPORTA_PROTON_CMD and PROTON_CMD.
- GUI Proton selection is a runtime mode, without explicit version/path UI.
- CLI passes default preferences to run_mhf. Do not assume it uses GUI prefs.
- MhfConfig is serialized as JSON, Base64-encoded and passed to the helper's
  stdin using `--stdin-b64`, with EOF after the write.
- The helper loads mhfo.dll or mhfo-hd.dll and resolves mhDLL_Main. No mhf.exe
  is required by this helper path.
- run_mhf with wait_for_exit=false discards helper stdout/stderr and returns
  after spawning. GUI launch paths can then exit without knowing the outcome.
- Proton currently receives WINEPREFIX equal to compat-data root; review the
  distinction between compat-data root and its Windows `pfx` child.
- Source helper uses windows_subsystem=windows in release; the included PE
  is subsystem 2 (GUI). A console copy is only a diagnostic experiment.

Helper explicit source exit codes: 1 missing stdin-b64 flag, 2 stdin read,
3 Base64, 4 UTF-8, 5 JSON deserialization, 6 meze-butter::run error. A code
returned by Proton/cmd is not necessarily one of these helper codes.

Included helper and staged helper SHA256 match:
`f4894263f0382cc56528485b7ae474f8c8a2bf80987ceadb93354efc9b829d3b`.
Matching copies do not establish reproducibility from the current source.

## Diagnostic script and invocation

scripts/linux/proton-host-debug.sh is an opt-in experiment. It dispatches
Python/Proton to the host, forwards selected runtime variables, removes
WINEPREFIX, validates payload metadata, creates a separate console helper
copy, and attempts Windows input-file redirection through cmd.exe.

It is NOT a finished shared runtime implementation. The current cmd path
fails to create its output file. Review quoting, inherited environment,
console behavior and Windows working directory instead of assuming success.
Temporary input contains credentials; normal exit cleans it up, but forced
termination can leave files behind. Never publish or print the input.
Console helper stderr may include sensitive values; sanitize shared output.

The maintainer applied incremental Python replacements locally. Read their
actual script; it may differ slightly from this checkpoint. Backups exist.

Run inside mhfz-dev, using the same terminal for exports and launch:

```bash
cd /home/deck/Progetti/Mezeporta-steamos
export MEZEPORTA_PROTON_CMD="$PWD/scripts/linux/proton-host-debug.sh"
export MEZEPORTA_HOST_PROTON="$HOME/.local/share/Steam/steamapps/common/Proton - Experimental/proton"
npm run tauri:dev -- --target x86_64-unknown-linux-gnu --config src-tauri/tauri.linux.conf.json --no-watch
```

Diagnostic log: ~/.local/state/mezeporta/proton-host.log.

## Evidence from actual SteamOS tests

1. Host Proton executed and initialized the separate prefix, reporting
   upgrade from None to 11.0-100 and `ntsync: up and running`.
2. A synthetic pipe through distrobox-host-exec delivered all 20 bytes of
   MEZEPORTA_STDIN_TEST to host Python, with equality True.
3. Real launch input reaching host Python: 2428 bytes, valid Base64, UTF-8
   and JSON object. Metadata shows 33 fields including character/auth/server
   data, version, mutex_version, mhf_folder, font_path and launch preferences.
   This does NOT verify Windows helper input or schema compatibility.
4. Original helper through Unix pipe exited with code 5 without readable error.
5. Console helper through Unix pipe opened a blank console and remained
   running. Waiting for console input is a hypothesis, not a proven cause.
6. Synthetic JSON `{}` (Base64 e30=) through cmd.exe file redirection on the
   interactive host terminal succeeded in reaching the helper. Exit code 5,
   output: `error parsing config data: missing field char_id at line 1 column 2`.
7. Automatic wrapper redirection failed, including after explicit Windows cd:
   `Helper output file exists: False`, `Proton host exit status: 1`.
   Latest reported attempt: 2026-10-09 15:23:02 Europe/Paris.
   Do not interpret this as a successful JSON handoff or a game error.

## Next isolating test — proposed, NOT executed yet

Reproduce the successful synthetic host command with stdin /dev/null and
stdout/stderr redirected, to compare with automatic launch conditions:

```bash
cd "$HOME/Applications/MH Frontier Z"
printf '%s' 'e30=' > Mezeporta/stdin-probe.txt
STEAM_COMPAT_DATA_PATH="$PWD/Mezeporta/ProtonData" \
STEAM_COMPAT_CLIENT_INSTALL_PATH="$HOME/.local/share/Steam" \
python3 "$HOME/.local/share/Steam/steamapps/common/Proton - Experimental/proton" \
run cmd.exe /d /c 'Mezeporta\bin\meze-deps-console-debug.exe --stdin-b64 < Mezeporta\stdin-probe.txt > Mezeporta\stdin-probe-headless.log 2>&1' \
</dev/null > Mezeporta/proton-probe-headless.log 2>&1
printf 'Exit code: %s\n' "$?"
cat Mezeporta/proton-probe-headless.log
cat Mezeporta/stdin-probe-headless.log
```

## Work requested from Codex

First isolate the failure of automatic cmd redirection using a minimal
reproduction and attributable diagnostics. Then verify MhfConfig semantics,
Linux-to-Windows paths, helper build provenance and DLL loading as needed.
Implement shared host Proton execution that preserves argument boundaries,
cwd, environment and helper configuration. Add meaningful runtime diagnostics,
correct compat-data/pfx handling and a permanent watcher exclusion. Later
implement library discovery and explicit Proton selection. Validate on the
maintainer's SteamOS before declaring launch fixed.

The inspection workspace cannot perform the real SteamOS/game/server test.
Only Bash/Python syntax and diff checks were run there for the diagnostic script.
