# Native Windows builds from SteamOS

Build Windows artifacts on a Windows runner through **Build Windows** in GitHub
Actions. This route does not require a local Windows machine or cross-compilation
toolchain on SteamOS. The Linux AppImage is a separate package.

## Run and download

1. Push reviewed application or build changes to `steamos-dev`; they start the
   workflow automatically.
2. For later builds, open **Actions → Build Windows → Run workflow**, select
   `steamos-dev` and start it. This is also the repository's default branch.
   With GitHub CLI authentication, the equivalent command is
   `gh workflow run windows-build.yml --ref steamos-dev`.
3. Download the completed run's `Mezeporta-windows-x86-<commit>` artifact.

The artifact contains an NSIS installer, a portable ZIP, `SHA256SUMS.txt` and
the source commit in `BUILD.txt`. It is retained for 30 days. The workflow does
not create a GitHub Release or sign binaries. Build success confirms compilation
and packaging; login and game launch still require a Windows runtime test.

## Packages

The launcher targets `i686-pc-windows-msvc` (x86) to match the 32-bit game's native
injection path. It also runs on 64-bit Windows. The Windows build does not use
the Linux host bridge or WebKit diagnostics.

The installer includes audio resources and can download/install WebView2 Runtime
when needed. The portable ZIP contains `Mezeporta.exe`, `audio/`, license and
usage notes; install WebView2 separately if absent. Place the portable contents
beside the game's `dat` directory, or select the game folder in the installed
launcher. Neither package contains the game client.

Artifacts are unsigned. Verify the commit and SHA-256 checksums before
distributing a tested build; Windows may show publisher/reputation prompts.

## Local Windows build

Install Node.js 22, Rust stable, Visual Studio C++ Build Tools with Windows SDK,
and WebView2 Runtime. From the repository root in PowerShell:

```powershell
rustup target add i686-pc-windows-msvc
npm ci
npm run tauri:build -- --ci --target i686-pc-windows-msvc --config src-tauri/tauri.windows.conf.json
```

Outputs are under `src-tauri/target/i686-pc-windows-msvc/release/`; the installer
is in `bundle/nsis/`. The workflow accepts the product or Cargo executable name,
packages it as `Mezeporta.exe` and creates checksums. A new push cancels an
outdated build of the same branch so artifacts correspond to the latest source.

`src-tauri/tauri.windows.conf.json` supplements the common configuration. The
existing `beforeBuildCommand` builds the frontend; `npm ci` preserves its
lockfile. This route does not execute `build-linux.mjs` or need Distrobox, Proton,
GTK or Steam Linux Runtime. Linux-to-Windows cross-compilation is not the
validated build route for this project.
