# Linux compatibility and host requirements

## Compatibility goal

Mezeporta's Linux release is an **x86_64 AppImage**. The project aims to make
this package usable across common desktop Linux distributions, but that is a
compatibility goal, not a promise that every distribution or desktop works.
At present, full launcher and game testing is documented only for the SteamOS
environment described in [SteamOS.md](SteamOS.md). Ubuntu, Debian, Fedora,
Arch outside the tested SteamOS build environment, and other distributions
still need direct testing.

| Environment | Status |
| --- | --- |
| SteamOS 3.8.28, x86_64, Desktop Mode and Gaming Mode, native 1920×1080 | Verified on the maintainer's Steam Machine |
| Ubuntu / Debian desktop | Not yet verified with the AppImage |
| Fedora desktop | Not yet verified |
| Arch Linux outside the documented SteamOS/Distrobox workflow | Not yet verified |
| Other x86_64 Linux distributions | Not yet verified |
| Linux systems that are not x86_64 | Not provided by this AppImage |

The SteamOS validation record, build details and Gaming Mode setup are in
[SteamOS.md](SteamOS.md). The AppImage is intended to start the Linux launcher;
it does not bundle Monster Hunter Frontier's game files.

## What the AppImage still needs from the host

AppImage packaging reduces installation work, but this package is not fully
self-contained. A compatible host must provide:

- An x86_64 Linux userspace with a compatible glibc and dynamic loader. The
  project's minimum glibc version has not yet been established across
  distributions.
- A working graphics stack and desktop session. Mesa/EGL and Wayland libraries
  are taken from the host in the current bundle so that the application does
  not mix those libraries with copies from its build environment. Driver,
  Vulkan, X11/XWayland and Wayland combinations outside SteamOS need testing.
- AppImage execution support, normally FUSE 2 compatibility, or a working
  `APPIMAGE_EXTRACT_AND_RUN=1` fallback supported by the AppImage runtime.
- For Linux launcher sound effects, host `gst-inspect-1.0` and
  `gst-launch-1.0`, GStreamer URI decoding, audio conversion, resampling and
  volume elements, plus an available PulseAudio or PipeWire sink. The sound
  effect implementation deliberately runs host GStreamer with AppImage
  library and plugin overrides removed. If host GStreamer or a sink is
  missing, sound effects may be unavailable; game launch does not depend on
  launcher sound playback.
- To launch the Windows game, Steam, a compatible Proton installation and the
  Steam Linux Runtime declared by that Proton build. The launcher bridges game
  startup to the host's Steam/Proton setup; Proton and the game are not bundled
  in the AppImage. See [SteamOS.md](SteamOS.md#runtime-architecture) for the
  verified runtime behavior.

The project currently provides dependency setup and verification scripts for
Ubuntu/Debian and Arch. They describe supported setup workflows, but their
existence does not mean the standalone AppImage has been validated on those
distributions. There is no Fedora-specific setup script yet. Review a script
before running it because its install mode uses the distribution package
manager and may request administrator privileges.

## Before reporting a distribution as supported

Record the distribution and release, architecture, desktop session, graphics
driver, AppImage runtime method, GStreamer version and audio backend. Then
check the launcher starts, settings persist, sound effects play without
freezing the launcher, and—where Steam/Proton is available—the game launches
and accepts keyboard, mouse and controller input. Record failures separately
from untested behavior. A successful launch on one machine is evidence for
that configuration, not for every release of the distribution.

When reporting an issue, include the distribution version and the relevant
application log. Remove passwords, tokens and other private configuration
before sharing logs. SteamOS-specific diagnostics and the verified baseline
are maintained in [SteamOS.md](SteamOS.md).
