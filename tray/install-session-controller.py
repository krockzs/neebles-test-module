#!/usr/bin/python3.13
"""Explicit, opt-in, host-user-only installer for Test Module's session helper."""
import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

NAME = "neebles-test-module-session-controller"
SRC = Path(__file__).resolve().parent / "session-controller.py"
TARGET = Path.home() / ".local/share/neebles/test-module/session-controller.py"
UNIT = Path.home() / ".config/systemd/user" / f"{NAME}.service"


def run(*args):
    subprocess.run(args, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise SystemExit("ERROR: ejecutar como usuario, sin sudo")
    if args.remove:
        run("systemctl", "--user", "disable", "--now", f"{NAME}.service")
        UNIT.unlink(missing_ok=True)
        run("systemctl", "--user", "daemon-reload")
        print("GREEN: controlador deshabilitado")
        return
    if not SRC.is_file():
        raise SystemExit("ERROR: falta session-controller.py")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    UNIT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=TARGET.parent, delete=False) as tmp:
        temp_path = Path(tmp.name)
        tmp.write(SRC.read_bytes())
    os.chmod(temp_path, 0o700)
    os.replace(temp_path, TARGET)
    unit = f'''[Unit]
Description=N.E.E.B.L.E.S. Test Module session controller
Before=neebles-tray-manager.service
PartOf=graphical-session.target
ConditionPathExists=/opt/neebles/modules/test-module/manifest.json

[Service]
Type=notify
NotifyAccess=main
ExecStart=/usr/bin/python3.13 {TARGET}
Restart=on-failure
RestartSec=2
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
'''
    UNIT.write_text(unit, encoding="utf-8")
    run("systemctl", "--user", "daemon-reload")
    run("systemctl", "--user", "enable", "--now", f"{NAME}.service")
    print("GREEN: controlador de Test Module instalado para la sesión KDE")
    print(f"GREEN: {TARGET}")
    print(f"GREEN: {UNIT}")


if __name__ == "__main__":
    main()
