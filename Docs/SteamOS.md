# SteamOS: installation, build and verified runtime

## Verified status — 13 October 2026

The maintainer tested the standalone AppImage in Desktop Mode and Gaming Mode
at native 1920×1080. Login, character selection, land entry, mouse, keyboard,
controller and normal shutdown worked with empty Steam launch options and no
external Proton proxy. The game remained running when the launcher closed.

Test environment: SteamOS 3.8.28, build 20260922.1, AMD graphics, kernel
6.18.50-valve2-1, Proton Experimental `experimental-11.0-20261001-x86_64` and
Steam Linux Runtime 4. The build used the `mhfz-appimage` Distrobox.

These are results on the maintainer's machine, not a guarantee for every driver,
server or game version. Higher resolutions, external televisions and the current
rebuilt portable tarball need separate validation. The code does not impose a
1080p cap or reduce the game resolution.

## Install and run

Keep the AppImage at a permanent path, make it executable and add that file as
a non-Steam shortcut. Leave launch options empty and compatibility-tool forcing
disabled. The launcher is native Linux; Proton runs the Windows game itself.

In launcher settings, select the game directory and **Wine Prefix: Proton**.
Install Proton Experimental and the Steam Linux Runtime it requires through
Steam. The bridge reads `toolmanifest.vdf` and reports missing prerequisites;
it does not silently fall back to raw host execution.

Proton compat data defaults to `<game>/Mezeporta/ProtonData`; its Wine prefix
is the `pfx` child. Configuration remains in the selected game directory.
Back up the prefix before manual maintenance; normal updates do not require
recreating it. The AppImage does not include the game client.

## Runtime architecture

AppRun stages `usr/bin/mezeporta-proton-host.sh` into a private directory under
`XDG_RUNTIME_DIR` (or the temporary-directory fallback), then exports
`MEZEPORTA_PROTON_CMD`. The bridge remains available after the launcher exits
and its temporary AppImage mount disappears.

For direct host execution it removes AppImage `PYTHONHOME`, `PYTHONPATH` and
`LD_LIBRARY_PATH`, then uses host Python. It removes `WINEPREFIX` before Proton,
which owns prefix creation. The game working directory, Steam identity and
rendering preferences are preserved.

All Proton setup and game-helper commands go through:

```text
<required-runtime>/_v2-entry-point --verb=run -- <proton> <arguments>
```

| Required tool AppID | Runtime directory |
| --- | --- |
| 4183110 | SteamLinuxRuntime_4 |
| 1628350 | SteamLinuxRuntime_sniper |
| 1391110 | SteamLinuxRuntime_soldier |

The bridge searches beside the resolved Proton installation, then under
`STEAM_COMPAT_CLIENT_INSTALL_PATH/steamapps/common`. Unsupported or missing
runtime requirements produce explicit errors. Installing only Proton is not
sufficient when its required runtime is absent.

The helper receives the unchanged base64 payload through a private temporary
file with mode 0600. Logs record field names and types, not authentication
values. The bridge associates the matching MHFZ window with the Steam shortcut
AppID for Gamescope. After game launch the launcher closes its window normally,
preserving the game instead of forcing application exit.

## Cause of the full-monitor loading freeze

The original host launch bypassed Steam Linux Runtime. The host lacked
32-bit `libXi.so.6`, despite having the 64-bit library. The game's 32-bit Wine
process could not initialize XInput2 and repeatedly attempted and cancelled
fullscreen cursor clipping. The trace recorded 722,204 iterations in about
50 seconds, followed by the game connection timing out.

The geometry boundary was reproducible: 1920×1079 and 1918×1080 loaded, whereas
1920×1080 froze under a 1920×1080 Gamescope display. The declared runtime made
XInput2 available and removed clipping refusals; native 1080p land entry and
input were then confirmed. This fixes the runtime dependency rather than
depending on smaller windows or upscaling.

The successful runtime trial used WineD3D. Earlier trials also exercised DXVK;
the runtime fix does not force either renderer. A false launcher WineD3D
preference does not necessarily override inherited `PROTON_USE_WINED3D=1`;
inspect the actual process environment when diagnosing renderer selection.
Renderer changes are separate from this fix.

## AppImage packaging and build

Bundled Wayland libraries are excluded because SteamOS supplies Mesa/EGL and
the matching Wayland libraries. Removing the build-container copies fixed the
original gray launcher with `EGL_BAD_PARAMETER`. GStreamer remains bundled.
This fix does not disable WebGL or force software rendering globally.

`scripts/build-linux.mjs` stages the bridge, injects an idempotent marked
AppRun block, repackages the sanitized AppImage and creates the portable tarball.
Both output paths honor `CARGO_TARGET_DIR`.

The Linux bridge's isolated contract tests use fake Proton/runtime executables;
they check manifest selection, private payload transport, exit codes, missing
runtime errors and paths containing spaces without touching a real prefix:

```bash
python3 scripts/linux/test_proton_host.py
```

Example inside the configured build Distrobox:

```bash
cd /home/deck/Progetti/Mezeporta-SteamOS
export CARGO_TARGET_DIR="$HOME/.cache/mezeporta-steamos-target"
npm ci
npm run tauri:build:linux
```

Outputs are under:

```text
$CARGO_TARGET_DIR/x86_64-unknown-linux-gnu/release/bundle/appimage/
$CARGO_TARGET_DIR/x86_64-unknown-linux-gnu/release/bundle/portable/
```

Without the override, the default root is `src-tauri/target`. Use the repository's
Linux dependency scripts for build prerequisites. Keep a working AppImage backup
before installing a new build; hashes identify an artifact, not every future
build of the same version.

## Logs, overrides and troubleshooting

| Variable | Purpose |
| --- | --- |
| MEZEPORTA_HOST_PROTON | Absolute path to the actual Proton script |
| MEZEPORTA_PROTON_CMD | Optional replacement host bridge |
| MEZEPORTA_DIRECT_HOST | AppImage sets 1; portable Distrobox uses host dispatch |
| MEZEPORTA_DEBUG_DIR | Override bridge log directory |
| MEZEPORTA_WEBKIT_DIAGNOSTICS | Set to 1 to enable JavaScript console output |

Default bridge log: `~/.local/state/mezeporta/proton-host.log`. Successful
invocations identify `Steam runtime:` and `Required runtime AppID:`. This log
updates when Proton operations occur, not just when the launcher opens.

WebKit diagnostics are opt-in, disabled for normal launches, and print a marker
plus console messages to stdout/stderr. Capture those streams when investigating
startup. An intermittent `window.__TAURI_IPC__` startup error was observed;
later diagnostic and normal launches succeeded. Its cause remains unestablished
and is not a second confirmed fix. Raw translation keys in that failure followed
from settings initialization failing.

GTK module notices and mixed-architecture Steam overlay preload warnings were
also present in successful runs. Their presence alone does not diagnose failure.
Image-preload warnings can mean missing server artwork without preventing play.
Never publish config files containing passwords, tokens or helper payloads.
Historical external test wrappers are not AppImage prerequisites.

## Portable Distrobox alternative

`launch-gaming-mode.sh` starts the portable launcher inside its configured
Distrobox, and the bridge dispatches Proton to the host and its required Steam
Linux Runtime. This alternative still requires Distrobox and host integration
tools. The shared runtime fix applies to both routes, but the current portable
package needs its own retest. The AppImage is the standalone validated package.

## References

- [Mezeporta upstream](https://github.com/LilButter/Mezeporta), original CLI-dev
  baseline `0d7712f99700ff643c834cc3fd668a4767ca5a05`.
- [Valve Steam Runtime documentation](https://github.com/ValveSoftware/steam-runtime/blob/master/README.md).
- Installed Proton `toolmanifest.vdf` and runtime `_v2-entry-point`.
- The captured Wine cursor trace and installed library inventory establish the
  clipping-loop diagnosis on the tested machine.
- [Tauri 1.6.8 initialization](https://github.com/tauri-apps/tauri/blob/tauri-v1.6.8/core/tauri/scripts/init.js).
