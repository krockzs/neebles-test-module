#!/usr/bin/python3.13
"""Opt-in user-session controller owned by Test Module.

This runs as a separate, explicitly enabled **user** service, never inside a
module's Bubblewrap runtime. It exposes only status/open for this one installed
module over a 0600 Unix socket; no arbitrary commands or paths are accepted.
A module runtime sees only this narrow socket, not Boss's administrative IPC.
"""

import json
import os
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

MODULE = "test-module"
UID = os.getuid()
RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{UID}"))
SOCKET_PATH = RUNTIME_DIR / "neebles" / f"{MODULE}-controller.sock"
LOCAL_SETTINGS = Path("/opt/neebles/shared/settings/local_settings_test-module.json")
DEFAULT_SETTINGS = Path("/opt/neebles/modules/test-module/settings/default.json")
BACKEND = Path("/opt/neebles/client/backend/neebles-backend")
OPEN_LOCK = threading.Lock()
STOP = threading.Event()


def bool_setting(key):
    defaults = json.loads(DEFAULT_SETTINGS.read_text(encoding="utf-8"))
    local = json.loads(LOCAL_SETTINGS.read_text(encoding="utf-8")) if LOCAL_SETTINGS.exists() else {}
    return local.get("tray", {}).get(key, defaults["tray"][key]) == "true"


def cli(*args, timeout=12):
    proc = subprocess.run([str(BACKEND), *args], capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout or "operation failed").strip()[:500])
    return proc.stdout.strip()


def is_open():
    data = json.loads(cli("modules", "runtime", "status", MODULE, timeout=6))
    if data.get("module") != MODULE:
        raise RuntimeError("unexpected runtime identity")
    return data.get("registered") is True


def dispatch(action):
    if action == "status":
        return {"ok": True, "opened": is_open()}
    if action == "open":
        with OPEN_LOCK:
            if is_open():
                return {"ok": True, "opened": True, "already_open": True}
            cli("modules", "action", MODULE, "open", timeout=20)
            return {"ok": True, "opened": True, "already_open": False}
    return {"ok": False, "error": "unsupported action"}


def handle(conn):
    conn.settimeout(24)
    try:
        credentials = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        _pid, uid, _gid = struct.unpack("3i", credentials)
        if uid != UID:
            raise PermissionError("user mismatch")
        with conn.makefile("rb") as reader:
            raw = reader.readline(2049)
        if len(raw) > 2048 or not raw.endswith(b"\n"):
            raise ValueError("invalid request frame")
        request = json.loads(raw)
        if not isinstance(request, dict) or set(request) != {"action"} or not isinstance(request["action"], str):
            raise ValueError("invalid controller request")
        result = dispatch(request["action"])
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, PermissionError) as error:
        result = {"ok": False, "error": str(error)[:500]}
    try:
        conn.sendall((json.dumps(result, separators=(",", ":")) + "\n").encode())
    except OSError:
        pass
    finally:
        conn.close()


def reconcile_on_login():
    # Boss and the desktop Tray Manager can start in different orders.
    # This finite retry repairs that session race only if the user opted in.
    if not (bool_setting("autostart") and bool_setting("visible")):
        return
    for _ in range(40):
        if STOP.is_set():
            return
        try:
            cli("tray", "reconcile", timeout=5)
            return
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            STOP.wait(2)
    print("Test Module: tray reconciliation unavailable after login", file=sys.stderr)


def main():
    if os.geteuid() == 0 or UID == 0:
        raise RuntimeError("controller must run as a regular desktop user")
    base = SOCKET_PATH.parent
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not base.is_dir() or base.is_symlink() or base.stat().st_uid != UID:
        raise RuntimeError("unsafe controller socket parent")
    if SOCKET_PATH.exists() or SOCKET_PATH.is_symlink():
        if not SOCKET_PATH.is_socket() or SOCKET_PATH.lstat().st_uid != UID:
            raise RuntimeError("refusing to replace non-owned controller socket")
        probe = socket.socket(socket.AF_UNIX)
        probe.settimeout(1)
        try:
            probe.connect(str(SOCKET_PATH))
        except OSError:
            SOCKET_PATH.unlink()
        else:
            raise RuntimeError("another controller is already running")
        finally:
            probe.close()
    with socket.socket(socket.AF_UNIX) as listener:
        listener.bind(str(SOCKET_PATH))
        os.chmod(SOCKET_PATH, 0o600)
        listener.listen(12)
        listener.settimeout(1)
        # Let systemd release neebles-tray-manager.service only after this
        # socket exists, eliminating the login start-order race.
        notify = os.environ.get("NOTIFY_SOCKET")
        if notify:
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sd:
                sd.sendto(b"READY=1", "\0" + notify[1:] if notify.startswith("@") else notify)
        signal.signal(signal.SIGTERM, lambda *_: STOP.set())
        signal.signal(signal.SIGINT, lambda *_: STOP.set())
        threading.Thread(target=reconcile_on_login, daemon=True).start()
        try:
            while not STOP.is_set():
                try:
                    conn, _ = listener.accept()
                except socket.timeout:
                    continue
                # The controller may receive a status check while an Open
                # request is active; isolate each bounded request.
                threading.Thread(target=handle, args=(conn,), daemon=True).start()
        finally:
            SOCKET_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
