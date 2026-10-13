"""Exercise the complete Bash bridge with fake runtime and fake Proton."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


BRIDGE = Path(__file__).with_name("proton-host-debug.sh")
RUNTIME_SCRIPT = '''import json, os, sys
from pathlib import Path
Path(os.environ["FAKE_RUNTIME_RECORD"]).write_text(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}))
assert sys.argv[1:3] == ["--verb=run", "--"]
os.execv(sys.argv[3], sys.argv[3:])
'''
PROTON_SCRIPT = '''import hashlib, json, os, stat, sys
from pathlib import Path
args = sys.argv[1:]
keys = ["PROTON_USE_WINED3D", "DISPLAY", "SteamGameId", "SteamAppId", "STEAM_COMPAT_DATA_PATH", "PYTHONHOME", "PYTHONPATH", "LD_LIBRARY_PATH", "WINEPREFIX", "PROTON_LOG", "WINEDEBUG"]
record = {"args": args, "cwd": os.getcwd(), "env": {key: os.environ.get(key) for key in keys}}
if "--config-b64-file" in args:
    value = args[args.index("--config-b64-file") + 1]
    assert chr(92) in value and not value.startswith("/")
    config = Path(value.replace(chr(92), "/"))
    record["input_path"] = str(config.resolve())
    record["mode"] = stat.S_IMODE(config.stat().st_mode)
    record["payload_sha"] = hashlib.sha256(config.read_bytes()).hexdigest()
Path(os.environ["FAKE_PROTON_RECORD"]).write_text(json.dumps(record))
print("synthetic helper response")
sys.exit(int(os.environ.get("FAKE_EXIT_STATUS", "0")))
'''


class BridgeContract(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="mezeporta-full-bridge-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.client = self.root / "Steam client with spaces"
        self.common = self.client / "steamapps/common"
        self.proton = self.common / "Proton - Experimental/proton"
        self.game = self.root / "Game folder with spaces"
        (self.game / "Mezeporta").mkdir(parents=True)
        self.runtime_record = self.root / "runtime.json"
        self.proton_record = self.root / "proton.json"
        self.logs = self.root / "debug"
        self.make_proton(self.proton)
        self.entry = self.make_runtime(self.common)
        self.tools = self.root / "tools"
        self.tools.mkdir()
        for name in ("xwininfo", "xprop"):
            tool = self.tools / name
            tool.write_text("#!/bin/sh\nexit 0\n")
            tool.chmod(0o700)
        self.env = dict(os.environ)
        self.env.update({
            "MEZEPORTA_DIRECT_HOST": "1",
            "MEZEPORTA_HOST_PROTON": str(self.proton),
            "STEAM_COMPAT_CLIENT_INSTALL_PATH": str(self.client),
            "STEAM_COMPAT_DATA_PATH": str(self.root / "test compat data"),
            "MEZEPORTA_DEBUG_DIR": str(self.logs),
            "PROTON_USE_WINED3D": "1", "DISPLAY": ":1",
            "SteamAppId": "0", "SteamGameId": "16046459896241061888",
            "FAKE_RUNTIME_RECORD": str(self.runtime_record),
            "FAKE_PROTON_RECORD": str(self.proton_record),
            "PYTHONHOME": "/nonexistent-appimage-python",
            "PYTHONPATH": "/nonexistent-appimage-python-path",
            "LD_LIBRARY_PATH": "/nonexistent-appimage-library-path",
            "WINEPREFIX": "/wrong-inherited-prefix",
            "PATH": str(self.tools) + os.pathsep + os.environ["PATH"],
        })
        for key in ("PROTON_LOG", "WINEDEBUG"):
            self.env.pop(key, None)

    def make_proton(self, path, runtime_id="4183110"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!" + sys.executable + "\n" + PROTON_SCRIPT)
        path.chmod(0o700)
        (path.parent / "toolmanifest.vdf").write_text(
            '"manifest" { "require_tool_appid" "' + runtime_id + '" }\n')

    def make_runtime(self, common, name="SteamLinuxRuntime_4"):
        path = common / name / "_v2-entry-point"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!" + sys.executable + "\n" + RUNTIME_SCRIPT)
        path.chmod(0o700)
        return path

    def run_bridge(self, args, payload=b""):
        return subprocess.run(["bash", str(BRIDGE), *args], input=payload,
                              env=self.env, cwd=self.game, capture_output=True)

    def test_setup_wrapped_runtime_exit_and_clean_environment(self):
        self.env["FAKE_EXIT_STATUS"] = "37"
        args = ["run", "reg", "query", r"HKCU\Software\Wine\DirectInput"]
        result = self.run_bridge(args)
        self.assertEqual(result.returncode, 37, result.stderr)
        outer = json.loads(self.runtime_record.read_text())
        self.assertEqual(outer["argv"], ["--verb=run", "--", str(self.proton), *args])
        data = json.loads(self.proton_record.read_text())
        self.assertEqual(data["args"], args)
        self.assertEqual(data["cwd"], str(self.game))
        self.assertEqual(data["env"]["PROTON_USE_WINED3D"], "1")
        self.assertEqual(data["env"]["DISPLAY"], ":1")
        for key in ("PYTHONHOME", "PYTHONPATH", "LD_LIBRARY_PATH", "WINEPREFIX", "PROTON_LOG", "WINEDEBUG"):
            self.assertIsNone(data["env"][key])

    def test_helper_payload_private_transport_cleanup_and_exit(self):
        self.env["FAKE_EXIT_STATUS"] = "5"
        secret = "synthetic-password-DO-NOT-LOG"
        payload = base64.b64encode(json.dumps({"user_password": secret, "char_id": 3}).encode()) + b"\n"
        args = ["run", str(self.game / "meze-deps.exe"), "--stdin-b64"]
        result = self.run_bridge(args, payload)
        self.assertEqual(result.returncode, 5, result.stderr)
        data = json.loads(self.proton_record.read_text())
        self.assertNotIn("--stdin-b64", data["args"])
        self.assertIn("--config-b64-file", data["args"])
        self.assertEqual(data["payload_sha"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(data["mode"], 0o600)
        self.assertFalse(Path(data["input_path"]).exists())
        self.assertEqual(data["env"]["SteamAppId"], "3736107586")
        log = (self.logs / "proton-host.log").read_text()
        self.assertNotIn(secret, log)
        self.assertNotIn(payload.decode().strip(), log)
        self.assertIn("synthetic helper response", log)
        self.assertIn("Proton host exit status: 5", log)

    def test_adjacent_runtime_in_alternate_library(self):
        external_common = self.root / "Other Steam library/steamapps/common"
        self.proton = external_common / "Proton - Experimental/proton"
        self.make_proton(self.proton)
        preferred = self.make_runtime(external_common)
        self.env["MEZEPORTA_HOST_PROTON"] = str(self.proton)
        self.assertEqual(self.run_bridge(["run", "reg", "query"]).returncode, 0)
        self.assertIn(str(preferred), (self.logs / "proton-host.log").read_text())

    def test_external_proton_falls_back_to_client_runtime(self):
        self.proton = self.root / "Custom Proton distribution/proton"
        self.make_proton(self.proton)
        self.env["MEZEPORTA_HOST_PROTON"] = str(self.proton)
        self.assertEqual(self.run_bridge(["run", "reg", "query"]).returncode, 0)
        self.assertIn(str(self.entry), (self.logs / "proton-host.log").read_text())

    def test_declared_sniper_is_selected(self):
        self.make_proton(self.proton, "1628350")
        sniper = self.make_runtime(self.common, "SteamLinuxRuntime_sniper")
        self.assertEqual(self.run_bridge(["run", "reg", "query"]).returncode, 0)
        self.assertIn(str(sniper), (self.logs / "proton-host.log").read_text())

    def test_unknown_runtime_never_launches_target(self):
        self.make_proton(self.proton, "9999999")
        self.assertNotEqual(self.run_bridge(["run", "reg", "query"]).returncode, 0)
        self.assertFalse(self.runtime_record.exists())
        self.assertFalse(self.proton_record.exists())
        self.assertIn("Unsupported Steam runtime", (self.logs / "proton-host.log").read_text())

    def test_missing_runtime_never_falls_back_to_host(self):
        self.entry.unlink()
        self.assertNotEqual(self.run_bridge(["run", "reg", "query"]).returncode, 0)
        self.assertFalse(self.proton_record.exists())
        self.assertIn("not installed or executable", (self.logs / "proton-host.log").read_text())

    def test_missing_manifest_never_launches_target(self):
        (self.proton.parent / "toolmanifest.vdf").unlink()
        self.assertNotEqual(self.run_bridge(["run", "reg", "query"]).returncode, 0)
        self.assertFalse(self.runtime_record.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
