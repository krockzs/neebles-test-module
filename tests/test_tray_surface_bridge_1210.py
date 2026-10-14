"""1.2.10: unprivileged Tray provider must consume canonical, owner-scoped projection."""
import importlib.util
import json
import socket
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "tray/tray-provider.py"
spec = importlib.util.spec_from_file_location("tm1210tray", SOURCE)
tray = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"tkinter": types.ModuleType("tkinter")}):
    spec.loader.exec_module(tray)


def reply(state="closed", available=True, enabled=True, owner="test-module", item="open.tray"):
    return {"type":"surface_snapshot", "tray_id":owner, "item_id":item,
            "enabled":enabled,"runtime_state":state,"open_available":available}

class TraySurfaceBridgeTests(unittest.TestCase):
    def test_status_only_from_governor(self):
        self.assertEqual(tray.authoritative_open_snapshot(reply()),
                         {"opened":False,"available":True})
        self.assertEqual(tray.authoritative_open_snapshot(reply(available=False)),
                         {"opened":False,"available":False})
        self.assertEqual(tray.authoritative_open_snapshot(reply(enabled=False)),
                         {"opened":False,"available":False})
        for state in ("opening", "open"):
            self.assertEqual(tray.authoritative_open_snapshot(reply(state,False)),
                             {"opened":True,"available":False})

    def test_reject_foreign_owner_or_surface(self):
        for bad in (reply(owner="other"), reply(item="config.notify"),
                    {**reply(),"type":"settings_value"}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                tray.authoritative_open_snapshot(bad)

    def test_invalid_or_contradictory_state_fails_closed(self):
        for bad in (reply(state="invented"), reply(state="open",available=True),
                    reply(state="opening",available=True), reply(enabled="true"),
                    reply(available="true"), {**reply(),"open_available":None}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                tray.authoritative_open_snapshot(bad)

    def test_sent_messages_have_exact_owner_and_surface(self):
        left,right = socket.socketpair()
        try:
            tray.send_line(left, {"type":"surface_action","tray_id":tray.TRAY_ID,
                                  "item_id":tray.OPEN_SURFACE_ITEM,"action":"open"})
            line=right.recv(1024)
            self.assertEqual(json.loads(line),{"type":"surface_action","tray_id":"test-module",
                                               "item_id":"open.tray","action":"open"})
        finally:
            left.close();right.close()

    def test_no_service_dependency_in_production_provider(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("test-module-controller.sock",source)
        self.assertNotIn("systemctl",source)
        self.assertNotIn("neebles modules action",source)
        self.assertIn('"type": "surface_action"',source)
        self.assertIn('"type": "surface_query"',source)

if __name__ == "__main__": unittest.main()
