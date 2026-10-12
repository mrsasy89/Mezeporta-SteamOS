#!/usr/bin/env bash
# Diagnostic bridge for CLI-dev's MEZEPORTA_PROTON_CMD override.
# stdin belongs to meze-deps: validate in memory and forward unchanged.
set -euo pipefail
umask 077

log_dir="${MEZEPORTA_DEBUG_DIR:-${HOME}/.local/state/mezeporta}"
mkdir -p "$log_dir"
exec >>"$log_dir/proton-host.log" 2>&1
printf '\n[%s] Proton host invocation\n' "$(date -Is)"

: "${MEZEPORTA_HOST_PROTON:?Set the absolute host Proton script path}"
: "${STEAM_COMPAT_DATA_PATH:?Missing compat-data directory}"
: "${STEAM_COMPAT_CLIENT_INSTALL_PATH:?Missing Steam installation directory}"
command -v distrobox-host-exec >/dev/null

forward_env=(
  "STEAM_COMPAT_DATA_PATH=$STEAM_COMPAT_DATA_PATH"
  "STEAM_COMPAT_CLIENT_INSTALL_PATH=$STEAM_COMPAT_CLIENT_INSTALL_PATH"
)
for key in PROTON_USE_WINED3D WINEESYNC WINEFSYNC WINEDLLOVERRIDES DISPLAY XAUTHORITY SteamAppId SteamGameId SteamOverlayGameId; do
  if [[ -v $key ]]; then forward_env+=("$key=${!key}"); fi
done

# Python receives paths as arguments, not interpolated shell code. Its stdin
# is forwarded unchanged. Proton owns WINEPREFIX and creates compat-data/pfx.
status=0
distrobox-host-exec env "${forward_env[@]}" python3 -c '
import os, sys, base64, json, subprocess
cwd, proton = sys.argv[1:3]
if not os.path.isfile(proton):
    sys.exit("Host Proton script does not exist: " + proton)
os.chdir(cwd)
os.makedirs(os.environ["STEAM_COMPAT_DATA_PATH"], exist_ok=True)
os.environ.pop("WINEPREFIX", None)
print("Host cwd:", cwd, flush=True)
print("Proton:", proton, flush=True)
print("Compat data:", os.environ["STEAM_COMPAT_DATA_PATH"], flush=True)
args = sys.argv[3:]
print("Operation:", "helper stdin" if "--stdin-b64" in args else "runtime setup", flush=True)
command = [sys.executable, proton, *args]
if "--stdin-b64" in args:
    # Recupera il GameID del collegamento non Steam ricevuto da Distrobox.
    steam_game_id = os.environ.get("SteamGameId", "")
    if not steam_game_id.isdecimal() or int(steam_game_id) == 0:
        steam_game_id = os.environ.get("SteamOverlayGameId", "")
    if steam_game_id.isdecimal() and 0 < int(steam_game_id) < (1 << 64):
        game_id = int(steam_game_id)
        # Nei collegamenti non Steam, AppID occupa i 32 bit superiori.
        app_id = game_id >> 32 if game_id > 0xffffffff else game_id
        os.environ["SteamGameId"] = str(game_id)
        if os.environ.get("SteamAppId", "0") in ("", "0"):
            os.environ["SteamAppId"] = str(app_id)
        print("Steam shortcut AppID:", os.environ["SteamAppId"], flush=True)
    payload = sys.stdin.buffer.read()
    print("Helper stdin bytes:", len(payload), flush=True)
    try:
        config = json.loads(base64.b64decode(payload.strip(), validate=True).decode("utf-8"))
        if not isinstance(config, dict):
            raise ValueError("Expected object")
        print("Payload: valid base64 / UTF-8 / JSON object", flush=True)
        # Only field names and types; never print values or exception messages.
        for key, value in sorted(config.items()):
            print("Config field:", key, "type:", type(value).__name__, flush=True)
    except (ValueError, UnicodeError) as error:
        print("Payload validation failed:", type(error).__name__, flush=True)
        sys.exit(65)
    import tempfile, pathlib
    with tempfile.TemporaryDirectory(prefix="launch-", dir="Mezeporta") as tmp:
        folder = pathlib.Path(tmp)
        relative_folder = folder.relative_to(pathlib.Path.cwd())
        input_path = folder / "input.b64"
        input_path.write_bytes(payload)
        os.chmod(input_path, 0o600)

        option_index = args.index("--stdin-b64")
        windows_input = str(relative_folder / "input.b64").replace("/", chr(92))
        args[option_index:option_index + 1] = [
            "--config-b64-file",
            windows_input,
        ]
        command = [sys.executable, proton, *args]

        print("Transport: private config file to GUI helper", flush=True)
        with tempfile.TemporaryFile() as output_file:
            result = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=output_file,
                stderr=subprocess.STDOUT,
            )

            import re, shutil

            app_id = os.environ.get("SteamAppId", "")
            associate_windows = (
                app_id.isdecimal()
                and 0 < int(app_id) <= 0xffffffff
                and bool(os.environ.get("DISPLAY"))
                and shutil.which("xwininfo") is not None
                and shutil.which("xprop") is not None
            )

            if app_id and not associate_windows:
                print(
                    "Gamescope association unavailable: check DISPLAY and X11 tools",
                    flush=True,
                )

            tagged_windows = set()
            expected_class = (
                "(\"steam_app_" + app_id + "\" "
                "\"steam_app_" + app_id + "\")"
            )

            while result.poll() is None:
                if associate_windows:
                    try:
                        tree = subprocess.run(
                            ["xwininfo", "-root", "-tree"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            text=True,
                            timeout=2,
                        )

                        for line in tree.stdout.splitlines():
                            # Seleziona solo la finestra MHFZ di questo collegamento.
                            match = re.match(
                                r"\s*(0x[0-9a-fA-F]+)\s+"
                                r"\"[^\"]*MONSTER HUNTER FRONTIER[^\"]*\":",
                                line,
                                re.IGNORECASE,
                            )

                            if not match or expected_class not in line:
                                continue

                            window_id = match.group(1)
                            if window_id in tagged_windows:
                                continue

                            tagged = subprocess.run(
                                [
                                    "xprop",
                                    "-id",
                                    window_id,
                                    "-f",
                                    "STEAM_GAME",
                                    "32c",
                                    "-set",
                                    "STEAM_GAME",
                                    app_id,
                                ],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=2,
                            )

                            if tagged.returncode == 0:
                                tagged_windows.add(window_id)
                                print(
                                    "Gamescope window associated:",
                                    window_id,
                                    "AppID:",
                                    app_id,
                                    flush=True,
                                )
                    except (OSError, subprocess.TimeoutExpired):
                        # X11 o la finestra possono chiudersi durante uscita.
                        pass

                try:
                    result.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
            output_file.seek(0)
            process_output = output_file.read()

        print("Process output bytes:", len(process_output), flush=True)
        if process_output:
            sys.stdout.flush()
            sys.stdout.buffer.write(process_output)
            sys.stdout.buffer.flush()

    sys.exit(result.returncode if result.returncode >= 0 else 128 - result.returncode)
os.execv(sys.executable, command)
' "$PWD" "$MEZEPORTA_HOST_PROTON" "$@" || status=$?
printf 'Proton host exit status: %s\n' "$status"
exit "$status"
