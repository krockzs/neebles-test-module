#!/usr/bin/python3.13
"""Install the module-owned controller in the authenticated desktop user's systemd.

Never execute as root or from the module's isolated runtime. This installer is
an explicit *desktop-user* operation, not an undeclared Boss Lifecycle action.
"""

import argparse
import json
import os
import socket
import stat
import subprocess
import tempfile
import time
from pathlib import Path

MODULE = "test-module"
NAME = "neebles-test-module-session-controller"
SRC = Path("/opt/neebles/modules/test-module/tray/session-controller.py")
MANIFEST = SRC.parents[1] / "manifest.json"
UNIT = Path.home() / ".config/systemd/user" / f"{NAME}.service"
CONTROLLER_SOCKET = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "neebles/test-module-controller.sock"
EXPECTED_EXEC = f"ExecStart=/usr/bin/python3.13 {SRC}"
LEGACY_EXEC = f"ExecStart=/usr/bin/python3.13 {Path.home() / '.local/share/neebles/test-module/session-controller.py'}"


def systemctl(*args):
    return subprocess.run(("systemctl", "--user", *args), check=True,
                          text=True, capture_output=True)


def validate_user():
    if os.getuid() == 0 or os.geteuid() == 0:
        raise RuntimeError("el controlador pertenece al usuario de KDE: ejecutar SIN sudo")
    home = Path.home()
    if home.is_symlink() or not home.is_dir() or home.stat().st_uid != os.getuid():
        raise RuntimeError("HOME de escritorio no pertenece al usuario o es un enlace")
    if not os.environ.get("XDG_RUNTIME_DIR"):
        raise RuntimeError("no hay XDG_RUNTIME_DIR de la sesion del usuario")
    runtime = Path(os.environ["XDG_RUNTIME_DIR"])
    if runtime.is_symlink() or not runtime.is_dir() or runtime.stat().st_uid != os.getuid():
        raise RuntimeError("XDG_RUNTIME_DIR no es una sesion autenticada del usuario")
    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        raise RuntimeError("no hay bus de sesion de KDE (DBUS_SESSION_BUS_ADDRESS)")


def owned_dir(path):
    # A module must not traverse attacker-controlled symlinks while installing.
    if path.is_symlink():
        raise RuntimeError(f"directorio de systemd es un enlace: {path}")
    if path.exists():
        if not path.is_dir() or path.stat().st_uid != os.getuid():
            raise RuntimeError(f"directorio de systemd no pertenece al usuario: {path}")
    else:
        parent = path.parent
        if not parent.exists():
            owned_dir(parent)
        path.mkdir(mode=0o700)


def validate_existing_unit():
    if UNIT.is_symlink():
        raise RuntimeError("no se reemplaza una unidad systemd enlazada")
    if not UNIT.exists():
        return None
    metadata = UNIT.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid():
        raise RuntimeError("no se reemplaza una unidad systemd de propiedad desconocida")
    current = UNIT.read_text(encoding="utf-8")
    # Recognize only the installed-code unit and the documented 1.2.6 legacy
    # snapshot. Neither a unit name nor the caller's identity proves ownership.
    if not (EXPECTED_EXEC in current or LEGACY_EXEC in current):
        raise RuntimeError("unidad existente no declara un controlador reconocido")
    if current.count("ExecStart=") != 1 or any(
        token in current for token in ("ExecStartPre=", "ExecStartPost=", "ExecStopPost=", "ExecCondition=", "OnFailure=")
    ):
        raise RuntimeError("unidad existente tiene comandos adicionales no autorizados")
    return current


def desired_unit():
    return f'''[Unit]
Description=N.E.E.B.L.E.S. Test Module session controller
Before=neebles-tray-manager.service
PartOf=graphical-session.target
ConditionPathExists=/opt/neebles/modules/test-module/manifest.json

[Service]
Type=notify
NotifyAccess=main
{EXPECTED_EXEC}
Restart=on-failure
RestartSec=2
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
'''


def verify_module():
    if not SRC.is_file() or not MANIFEST.is_file():
        raise RuntimeError("Test Module no esta instalado completamente")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("name") != MODULE or not isinstance(manifest.get("version"), str):
        raise RuntimeError("identidad de Test Module invalida")
    return manifest["version"]


def verify_socket(timeout=5.0):
    limit = time.monotonic() + timeout
    reason = "no existe"
    while True:
        try:
            meta = CONTROLLER_SOCKET.lstat()
            if not stat.S_ISSOCK(meta.st_mode) or meta.st_uid != os.getuid() or stat.S_IMODE(meta.st_mode) != 0o600:
                raise RuntimeError("el socket no tiene propietario/tipo/modo esperado")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(2)
                client.connect(str(CONTROLLER_SOCKET))
                client.sendall(b'{"action":"status"}\n')
                client.shutdown(socket.SHUT_WR)
                with client.makefile("r", encoding="utf-8") as handle:
                    data = handle.readline(4096)
            response = json.loads(data)
            if not isinstance(response, dict) or response.get("ok") is not True \
                    or not isinstance(response.get("open_available"), bool) \
                    or response.get("runtime_state") not in ("closed", "opening", "open"):
                raise RuntimeError(f"el controlador responde, pero Governor no esta disponible: {response}")
            return response
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            reason = str(exc)
            if time.monotonic() >= limit:
                raise RuntimeError(f"el controlador no quedo listo: {reason}") from exc
            time.sleep(0.1)


def install():
    version = verify_module()
    owned_dir(UNIT.parent)
    old = validate_existing_unit()
    desired = desired_unit()
    if old != desired:
        # Atomic replacement; no raw write to a live systemd unit.
        fd, name = tempfile.mkstemp(prefix=".neebles-controller-", dir=UNIT.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(desired)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(name, 0o600)
            os.replace(name, UNIT)
        finally:
            Path(name).unlink(missing_ok=True)
    systemctl("daemon-reload")
    systemctl("enable", f"{NAME}.service")
    systemctl("restart", f"{NAME}.service")
    systemctl("is-active", "--quiet", f"{NAME}.service")
    status = verify_socket()
    print(f"GREEN: Test Module {version}, controlador systemd-user activo")
    print(f"GREEN: socket autenticado {CONTROLLER_SOCKET}")
    print(f"GREEN: Governor runtime_state={status['runtime_state']} open_available={status['open_available']}")


def remove():
    previous = validate_existing_unit()
    if previous is None:
        print("GREEN: la unidad ya no existe")
        return
    systemctl("disable", "--now", f"{NAME}.service")
    UNIT.unlink()
    systemctl("daemon-reload")
    print("GREEN: controlador deshabilitado y retirado")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--check", action="store_true", help="inspeccionar sin modificar")
    args = parser.parse_args()
    validate_user()
    if args.remove and args.check:
        parser.error("--check y --remove son excluyentes")
    if args.check:
        verify_module()
        validate_existing_unit()
        status = verify_socket(timeout=0.1)
        print(f"GREEN: controlador operativo; {status}")
    elif args.remove:
        remove()
    else:
        install()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"ERROR: instalacion del controlador: {exc}") from exc
