"""Offline regressions for the explicit KDE-user 1.2.9 controller finalizer.

No systemd units or sockets in the current desktop are modified.
"""
import importlib.util
import json
import os
import socket
import stat
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "tray/install-session-controller.py"
spec = importlib.util.spec_from_file_location("tm129_controller_install", SOURCE)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class ControllerInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tm129-")
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.src = base / "opt/neebles/modules/test-module/tray/session-controller.py"
        self.src.parent.mkdir(parents=True)
        self.src.write_text("# test controller\n")
        self.manifest = self.src.parents[1] / "manifest.json"
        self.manifest.write_text(json.dumps({"name": "test-module", "version": "1.2.9"}))
        self.unit = base / "home/.config/systemd/user/neebles-test-module-session-controller.service"
        self.sock = base / "runtime/neebles/test-module-controller.sock"
        self.override = patch.multiple(installer,
            SRC=self.src, MANIFEST=self.manifest, UNIT=self.unit, CONTROLLER_SOCKET=self.sock,
            EXPECTED_EXEC=f"ExecStart=/usr/bin/python3.13 {self.src}",
            LEGACY_EXEC=f"ExecStart=/usr/bin/python3.13 {base / 'home/.local/share/neebles/test-module/session-controller.py'}")
        self.override.start()
        self.addCleanup(self.override.stop)
        self.systemctl_mock = patch.object(installer, "systemctl")
        self.sys = self.systemctl_mock.start()
        self.addCleanup(self.systemctl_mock.stop)
        self.verify_mock = patch.object(installer, "verify_socket", return_value={"runtime_state": "closed", "open_available": True})
        self.verify = self.verify_mock.start()
        self.addCleanup(self.verify_mock.stop)

    def test_new_install_creates_owned_atomic_unit_and_validates_socket(self):
        installer.install()
        self.assertIn(installer.EXPECTED_EXEC, self.unit.read_text())
        self.assertEqual(stat.S_IMODE(self.unit.stat().st_mode), 0o600)
        self.assertEqual(self.sys.call_count, 4)
        self.assertEqual(self.sys.call_args_list[0].args, ("daemon-reload",))
        self.assertEqual(self.sys.call_args_list[1].args, ("enable", f"{installer.NAME}.service"))
        self.assertEqual(self.sys.call_args_list[2].args, ("restart", f"{installer.NAME}.service"))
        self.verify.assert_called_once()

    def test_uninstall_then_reinstall_recreates_absent_unit(self):
        installer.install()
        installer.remove()
        self.assertFalse(self.unit.exists())
        installer.install()
        self.assertTrue(self.unit.is_file())
        self.assertIn(installer.EXPECTED_EXEC, self.unit.read_text())

    def test_idempotent_repeated_install(self):
        installer.install()
        first = self.unit.read_bytes()
        installer.install()
        self.assertEqual(first, self.unit.read_bytes())
        self.assertEqual(self.verify.call_count, 2)

    def test_refuse_foreign_unit(self):
        self.unit.parent.mkdir(parents=True)
        self.unit.write_text("[Service]\nExecStart=/bin/sh -c evil\n")
        with self.assertRaisesRegex(RuntimeError, "no declara un controlador"):
            installer.install()
        self.assertEqual(self.sys.call_count, 0)

    def test_refuse_unit_with_an_additional_exec_hook(self):
        self.unit.parent.mkdir(parents=True)
        self.unit.write_text(installer.desired_unit()+"ExecStartPre=/usr/bin/touch /tmp/not-allowed\n")
        with self.assertRaisesRegex(RuntimeError, "comandos adicionales"):
            installer.install()
        self.assertEqual(self.sys.call_count, 0)

    def test_refuse_symlink_unit(self):
        self.unit.parent.mkdir(parents=True)
        another = self.unit.parent / "foreign"
        another.write_text(installer.desired_unit())
        self.unit.symlink_to(another)
        with self.assertRaisesRegex(RuntimeError, "enlazada"):
            installer.install()
        self.assertEqual(self.sys.call_count, 0)

    def test_fail_if_module_not_installed(self):
        self.manifest.unlink()
        with self.assertRaisesRegex(RuntimeError, "no esta instalado"):
            installer.install()
        self.assertEqual(self.sys.call_count, 0)

    def test_remove_requires_owned_unit(self):
        installer.remove()
        self.assertEqual(self.sys.call_count, 0)
        installer.install()
        installer.remove()
        self.assertFalse(self.unit.exists())
        self.assertEqual(self.sys.call_args_list[-2].args, ("disable", "--now", f"{installer.NAME}.service"))

    def test_legacy_known_unit_can_be_migrated(self):
        self.unit.parent.mkdir(parents=True)
        self.unit.write_text("[Service]\n"+installer.LEGACY_EXEC+"\n")
        installer.install()
        self.assertIn(installer.EXPECTED_EXEC, self.unit.read_text())

    def test_controller_socket_status_real_unix_protocol(self):
        self.verify_mock.stop()
        self.verify = None
        self.sock.parent.mkdir(parents=True)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind(str(self.sock))
            listener.listen(1)
            os.chmod(self.sock, 0o600)
            seen = []
            def accept():
                peer, _ = listener.accept()
                with peer:
                    with peer.makefile("rb") as r:
                        seen.append(r.readline())
                    peer.sendall(b'{"ok":true,"runtime_state":"closed","open_available":true}\n')
            thread = threading.Thread(target=accept)
            thread.start()
            try:
                self.assertEqual(installer.verify_socket(timeout=1)["open_available"], True)
                self.assertEqual(seen, [b'{"action":"status"}\n'])
            finally:
                thread.join(timeout=2)
        self.sock.unlink()


if __name__ == "__main__":
    unittest.main()
