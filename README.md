# Mezeporta SteamOS

Mezeporta is a Monster Hunter Frontier launcher for Erupe community servers,
supporting 19 versions across all game branches. This fork focuses on running
the launcher and Windows game client on SteamOS through Proton's required
Steam Linux Runtime. The standalone AppImage runs directly on SteamOS;
Distrobox is used for building it and for the alternative portable package.

It is based on [LilButter/Mezeporta](https://github.com/LilButter/Mezeporta).
Active SteamOS development is maintained on the `steamos-dev` branch.

> [!IMPORTANT]
> The AppImage has been tested in Desktop Mode and Gaming Mode at native
> **1920×1080**, including land entry, mouse, keyboard, controller and normal
> shutdown. Proton Experimental runs through its declared Steam Linux Runtime.
> Resolutions above 1080p have not yet been tested.

## SteamOS status

| Area | Status |
| --- | --- |
| Launcher build and startup in an Arch Distrobox | Verified |
| Login, character selection and game launch in Desktop Mode | Verified |
| Proton Experimental through its required Steam Linux Runtime | Verified |
| Paths containing spaces | Verified |
| Native KDE folder picker on SteamOS | Verified |
| Hidden helper transport without a console window | Verified |
| Standalone AppImage without an external Proton proxy | Verified |
| Gaming Mode / Gamescope at native 1920×1080 | Verified |
| Land entry, mouse, keyboard and controller | Verified |
| Launcher shutdown while the game remains running | Verified |
| Higher resolutions and external televisions | Not yet tested |
| Current rebuilt portable package | Generated; needs its own runtime retest |
| Native Windows packaging | GitHub Actions workflow provided |

See [Docs/SteamOS.md](Docs/SteamOS.md) for the implementation notes and
requirements, implementation notes, troubleshooting and validation evidence.

## SteamOS AppImage: recommended installation

1. Keep the AppImage in a permanent directory and make it executable:
   `chmod +x Mezeporta-SteamOS.AppImage`.
2. Open it in Desktop Mode, select the MHFZ game directory and set
   **Wine Prefix: Proton** in launcher settings.
3. Install Proton Experimental and its required Steam Linux Runtime through
   Steam. The tested Experimental version requires **Steam Linux Runtime 4.0**.
4. Add the AppImage as a non-Steam shortcut. Point directly to the AppImage,
   leave **Launch Options empty**, and leave **Force the use of a specific
   Steam Play compatibility tool disabled**. The native Linux launcher selects
   Proton for the Windows game itself.
5. Launch that shortcut in Gaming Mode. Native 1920×1080 has been verified.

The AppImage includes its host bridge and stages it outside the temporary mount
so the game can outlive the launcher. No external test proxy or Distrobox is
needed to run this package. Game files and configuration remain in the selected
game directory; the AppImage does not contain the game client.

See [Docs/Windows.md](Docs/Windows.md) to build native Windows packages from
SteamOS through GitHub Actions.

## How to run

> [!NOTE]
> Game Dlls must be [unpacked](#unpacking-dlls) for the launcher to work.

Windows and Linux: place the launcher files in the game directory beside the
`dat` folder.

Your folder should look like this:

Windows:
```text
GameFolder/
  /dat
  Mezeporta.exe
  mhf.ini
  mhfo.dll
  xinput1_3.dll
```

Or Linux:
```text
GameFolder/
  /dat
  /Mezeporta
  mezeporta-bin
  run-mezeporta.sh
  mhf.ini
  mhfo.dll
  xinput1_3.dll
```

On Linux, make the launcher script and binary executable:
```bash
chmod +x run-mezeporta.sh mezeporta-bin
```

Launch command:
```bash
./run-mezeporta.sh
```

_FOR S7K version move ALL files from the provided folder into the game directory with the launcher._

### SteamOS development and portable Linux package

The currently verified development workflow runs the Linux launcher inside an
Arch Distrobox while the bridge enters the host and invokes Proton through its
required Steam Linux Runtime:

```bash
export MEZEPORTA_PROTON_CMD="$PWD/scripts/linux/proton-host-debug.sh"
export MEZEPORTA_HOST_PROTON="$HOME/.local/share/Steam/steamapps/common/Proton - Experimental/proton"

npm run tauri:dev -- \
  --target x86_64-unknown-linux-gnu \
  --config src-tauri/tauri.linux.conf.json
```

In **Settings**, select the game directory and set **Wine Prefix Mode** to
**Proton**. Proton compat data is stored at
`<game>/Mezeporta/ProtonData`; Proton owns its `pfx` child.

To build the portable package after a successful release build:

```bash
npm run tauri:build:linux:portable
```

The package is created under:

```text
src-tauri/target/x86_64-unknown-linux-gnu/release/bundle/portable/
```

For the AppImage, use `npm run tauri:build:linux` in the build Distrobox.
`CARGO_TARGET_DIR`, when set, controls both AppImage and portable output paths.
The AppImage is the package validated in Gaming Mode. The portable Distrobox
workflow has separate prerequisites and needs a retest of its current package;
see the SteamOS guide.

## Server Wrapper (Server Owners)
> [!NOTE]
> This is now OPTIONAL and you may connect to Erupe servers normally using the SignV1 option.

The [Wrapper](https://github.com/LilButter/Mezeporta-Wrapper) is a separate helper for Erupe servers and is required for the API server features to work.

(e.g. Mail, Distribution, Character Book, and Events)

## CLI Commands

| Command | Description | Default / Example |
| --- | --- | --- |
| `-v, --version <VERSION>` | Game version | `ZZ`, `G10.1`, `S7K`, `G1`, `F5`, `S6` |
| `-u, --username <USER>` | Login username | `player` |
| `-pw, --password <PASS>` | Login password | `secret` |
| `-s, --server <SERVER>` | Server hostname or IP | `192.168.1.100` |
| `-p1, --launcher-port <PORT>` | Launcher port | Default: `8080` for API, `53312` for Signv1 |
| `-p2, --game-port <PORT>` | Game/entrance port | Default: `53310` |
| `-t, --sign-server` | Use Signv1 authentication instead of API authentication | — |
| `-c, --character <SLOT>` | Character slot index (0-based) | `0` |
| `-HD, --hd` | Enable HD mode | Default: SD |
| `-fs, --friend-signature <SIG>` | Version/friend injection signature | `v1.52.79_04d16dc4` |
| `--list-versions` | List all available game versions | — |
| `--list-signatures` | List all version signatures for the selected game version | Requires `-v` |
| `--help` | Show CLI help | — |

### Examples

```text
# API server
Mezeporta -v ZZ -u player -pw secret -s 192.168.1.100 -c 0

# API server with custom ports and HD mode
Mezeporta -v S7K -u player -pw secret -s mezeporta.example.com -p1 8080 -p2 53310 -c 1 -HD

# Signv1 server
Mezeporta -v ZZ -u player -pw secret -s 192.168.1.100 -t -c 0

# Signv1 server with explicit sign port
Mezeporta -v ZZ -u player -pw secret -s 192.168.1.100 -t -p1 53312 -c 0

# Signv1 server with an explicit friend signature
Mezeporta -v ZZ -u player -pw secret -s 192.168.1.100 -t -c 0 -fs v1.52.79_04d16dc4

# List supported game versions
Mezeporta --list-versions

# List signatures for a specific game version
Mezeporta -v ZZ --list-signatures
```

## Version Support

| Branch | Versions
| --- | --- |
| Online | S6, S7K |
| Forward | F4, F5 |
| G | G1, G2, G3, G3.1, G3.2, GG, G5.1, G5.2, G6, G7, G9.1, G10.1 
| Z | Z1, ZZ |


## Offline-Mode
| Classic | PS4 |
| --- | --- |
| <img src="Docs/Assets/Classic/OfflineClassic.png" alt="Classic offline mode"> | <img src="Docs/Assets/PS4/OfflinePS4.png" alt="PS4 offline mode"> |

Initial boot will bring you to Offline-mode where you can add a server.

Last selected server will be used on next boot.

## Character Screen

| Classic | PS4 |
| --- | --- |
| <img src="Docs/Assets/Classic/OnlineClassic2.png" alt="Classic character screen"> | <img src="Docs/Assets/PS4/OnlinePS4.png" alt="PS4 character screen"> |

## Custom Images

Server Owners can provide the launcher with their own identity and artwork:
- Banners
- Headers
- Backgrounds
- ServerTag
- Cog
- Capcom
- Links
- Announcements
- News
- Server-patch
- Dialogue

Hunters can also provide their own images by enabling Offline-Images and placing the images in Mezeporta/Offline-Images/

(News, Announcements, Links, ServerTag and Banners are still provided by the server while Offline-Images are enabled.)

## Character Book
![Character book](Docs/Assets/BookFeature.png)

Character Book uses cached character savedata to provide equipment w/deco, currency, courses, itembox and playtime for the selected character.

Savedata cache is fetched at login and is cleared once the game starts. Savedata re-fetches only if cleared.

## Mail
![Mail viewer](Docs/Assets/MailFeature.png)

Mail shows player messages, system messages, guild invites, sender, dates, and item attachments.

## Distributions
![Distribution viewer](Docs/Assets/DistroFeature.png)

Distributions show unclaimed rewards with title, description, type, deadlines, color-coded text, item icons, and reward details.

## Friends List

| Small List | Large List |
| --- | --- |
| <img src="Docs/Assets/FriendsSmallFeature.png" alt="Small friends list"> | <img src="Docs/Assets/FriendsMaxFeature.png" alt="Large friends list"> |

Friends list contains your friends for the selected character also providing an online/offline icon. The pop-up changes dynamically with the amount of friends you have. MAX 50 :)

## Events
![Event information](Docs/Assets/EventFeature.png)

Active event buttons can appear in the footer area with their own information panels.
- MezFes
- Hunter Festa
- Diva
- Tenro/Tower
- Pallone Festival
- Conquest
- Hunting Tournament

## Settings

| Description open | Description closed |
| --- | --- |
| <img src="Docs/Assets/SettingsFeature1.png" alt="Settings page"> | <img src="Docs/Assets/SettingsFeature2.png" alt="Linux settings page"> |

The Settings page provides options ranging from launcher specific settings like launcher resolution or font, all the way to advanced graphics, audio, wine-prefix, and more.

## Patching

Mezeporta has multi-server patch support!
- Checks the selected server for patch information.
- Compares patch data against the selected client folder and checks cached patches to reuse if the e-tag/manifest matches.
- Renames any original files to have the extension .mezeold (if previously patched, it will restore to original files first before applying the new patch)
- Downloads missing or outdated files provided by the wrapper.
- Caches patch files under Mezeporta/Servers

## Unpacking Dlls

To unpack the dlls use [OllyDbg](https://ollydbg.net/download.htm)

You will also need the [CodeDoctor](https://github.com/JackAston/OllyDbg1plugins/tree/master/CodeDoctor%20v0.90) plugin.
- Step 1: Move `CodeDoctor.dll` and `CodeDoctor.ini` into `OllyDbg/Plugins` folder.
- Step 2: Open OllyDbg and load the game dll.
- Step 3: Navigate to `Plugins` then `CodeDoctor` and select `Unpack AsProtect`.
- Step 4: Move the unpacked dll into the game folder.
- Step 5: Happy Hunting!


## Windows Development

Requirements:

- Windows, Node.js 22 and npm.
- Rust with the `i686-pc-windows-msvc` target.
- Visual Studio C++ Build Tools and a Windows SDK.
- WebView2 Runtime for running the launcher.

Setup:

```powershell
npm ci
rustup target add i686-pc-windows-msvc
```

Dev mode for styling/Frontend:

```powershell
npm run tauri:dev
```

Build:

```powershell
npm run tauri:build -- --ci --target i686-pc-windows-msvc --config src-tauri/tauri.windows.conf.json
```

Windows packages target x86 to match the 32-bit game and also run on 64-bit
Windows. From SteamOS, open GitHub **Actions → Build Windows → Run workflow**
on `steamos-dev`. The workflow uploads an NSIS installer, a portable ZIP and
SHA-256 checksums; it does not publish a release. See
[Docs/Windows.md](Docs/Windows.md) for details.

## WSL Linux Development

WSL can be used from Windows to test or build the Linux launcher.

Linux and WSL builds need `src-tauri/bin/meze-deps.exe` because the Linux
launcher starts the Windows game client through Wine or Proton. A precompiled
32-bit Windows GUI helper is included.

From Windows:

```powershell
npm install
rustup target add i686-pc-windows-msvc
npm run meze-deps:build
```

Inside WSL, install and verify Linux build dependencies:

```bash
npm install
./scripts/linux/install-build-deps-ubuntu.sh --install
./scripts/linux/install-build-deps-ubuntu.sh --verify
```

Run through WSL:

```powershell
npm run tauri:dev:linux:wsl
```

Run through WSL with the GPU helper for hardware acceleration:

```powershell
npm run tauri:dev:linux:wsl-gpu
```

Build through WSL:

```powershell
npm run tauri:build:linux:wsl
```

Build Tarball for linux through WSL:
```bash
npm run tauri:build:linux:portable:wsl
```

Optional WSL variables:

- `MEZEPORTA_WSL_DISTRO`: WSL distro name.
- `MEZEPORTA_WSL_GPU_ADAPTER`: GPU adapter name used by the WSL GPU helper.

## Native Linux Development

Requirements:

- Node.js and npm.
- Rustup.
- WebKitGTK and JavaScriptCoreGTK development packages.
- GStreamer packages for UI audio.
- The included 32-bit Windows helper at `src-tauri/bin/meze-deps.exe`.

Ubuntu-based systems:

```bash
./scripts/linux/install-build-deps-ubuntu.sh --install
./scripts/linux/install-build-deps-ubuntu.sh --verify
```

Arch-based systems:

```bash
./scripts/linux/install-build-deps-arch.sh --install
./scripts/linux/install-build-deps-arch.sh --verify
```

Dev mode for styling/Frontend:

```bash
npm run tauri:dev:linux
```

Build for AppImage and Deb:

```bash
npm run tauri:build:linux
```
Build Tarball for linux:
```bash
npm run tauri:build:linux:portable
```

The full Linux build attempts to create AppImage and Debian packages before
creating the portable archive. If AppImage bundling is unavailable on the
current system but the release binary compiled successfully, the portable-only
command can still package that release binary.
