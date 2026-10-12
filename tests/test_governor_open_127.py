"""Regression tests for Test Module 1.2.7 authoritative Governor Open projection."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "tray/session-controller.py"
spec = importlib.util.spec_from_file_location("neebles_tm127_controller", SOURCE)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def projection(state, available, name="test-module"):
    return json.dumps([{"name": name, "runtime_state": state, "open_available": available}])

class GovernorOpenTests(unittest.TestCase):
    def test_authoritative_closed_and_available(self):
        with patch.object(controller, "cli", return_value=projection("closed", True)) as cli:
            self.assertEqual(controller.governor_open_snapshot(),
                             {"runtime_state": "closed", "open_available": True})
            cli.assert_called_once_with("boss", "surface-model", timeout=6)

    def test_opening_and_open_are_not_available(self):
        for state in ("opening", "open"):
            with self.subTest(state=state), patch.object(controller, "cli", return_value=projection(state, False)):
                result = controller.dispatch("status")
                self.assertTrue(result["opened"])
                self.assertFalse(result["open_available"])
                self.assertEqual(result["runtime_state"], state)

    def test_closed_but_disabled_is_not_available(self):
        with patch.object(controller, "cli", return_value=projection("closed", False)) as cli:
            result = controller.dispatch("status")
            self.assertFalse(result["opened"])
            self.assertFalse(result["open_available"])
            denied = controller.dispatch("open")
            self.assertFalse(denied["ok"])
            self.assertIn("not available", denied["error"])
            self.assertEqual(cli.call_count, 2)

    def test_open_when_already_running_is_noop(self):
        for state in ("opening", "open"):
            with self.subTest(state=state), patch.object(controller, "cli", return_value=projection(state, False)) as cli:
                result = controller.dispatch("open")
                self.assertTrue(result["ok"])
                self.assertTrue(result["already_open"])
                cli.assert_called_once_with("boss", "surface-model", timeout=6)

    def test_open_invokes_governor_once_then_rechecks(self):
        answers = iter([projection("closed", True), "", projection("open", False)])
        with patch.object(controller, "cli", side_effect=lambda *a, **kw: next(answers)) as cli:
            result = controller.dispatch("open")
            self.assertEqual(result, {"ok": True, "opened": True,
                                      "already_open": False, "open_available": False})
            self.assertEqual(cli.call_args_list[1].args,
                             ("modules", "action", "test-module", "open"))

    def test_fail_closed_on_invalid_or_foreign_projection(self):
        invalid = [
            "{}", "[]", projection("closed", True, "foreign-module"),
            projection("invalid", True), projection("open", True),
            json.dumps([{"name": "test-module", "runtime_state": "closed"}]),
        ]
        for data in invalid:
            with self.subTest(data=data), patch.object(controller, "cli", return_value=data):
                with self.assertRaises(RuntimeError):
                    controller.governor_open_snapshot()

    def test_unknown_action_rejected(self):
        self.assertFalse(controller.dispatch("invalid")["ok"])

if __name__ == "__main__":
    unittest.main()
