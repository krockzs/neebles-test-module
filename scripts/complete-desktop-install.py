#!/usr/bin/env python3
"""Complete a Boss-installed Test Module in the current KDE user session.

Without a generic Boss Install capability for systemd-user, run this explicitly
as the desktop user after Boss UI publishes the module. Never use sudo.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/opt/neebles/modules/test-module")
HELPER = ROOT / "tray/install-session-controller.py"


def call(argv):
    return subprocess.run(argv, check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--install-with-boss", action="store_true",
                   help="instalar el modulo usando la CLI oficial antes de completar el controlador")
    p.add_argument("--enable", action="store_true",
                   help="activar el modulo via CLI gobernada despues del setup")
    p.add_argument("--reconcile", action="store_true",
                   help="pedir al Tray Manager la reconciliacion tras el setup")
    args = p.parse_args()
    if os.geteuid() == 0 or os.getuid() == 0:
        p.error("ejecutar como usuario KDE, no con sudo")
    if not os.environ.get("XDG_RUNTIME_DIR") or not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        p.error("requiere la sesion grafica autenticada del usuario")
    if args.install_with_boss:
        print("=== BOSS: instalar Test Module ===", flush=True)
        call(["neebles", "modules", "install", "test-module"])
    if not HELPER.is_file():
        p.error("el modulo aun no existe en /opt/neebles/modules/test-module; instalar primero con Boss")
    print("=== SESION KDE: preparar controlador ===", flush=True)
    call([sys.executable, str(HELPER)])
    if args.enable:
        print("=== BOSS: habilitar modulo ===", flush=True)
        call(["neebles", "modules", "enable", "test-module"])
    if args.reconcile:
        print("=== TRAY: reconciliar ===", flush=True)
        call(["neebles", "tray", "reconcile"])
    print("GREEN: setup de escritorio completado; verificar visualmente el Tray", flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ERROR: fase fallida: {exc}") from exc
