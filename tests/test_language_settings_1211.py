"""Candidate contract tests; no graphical session or external Boss required."""
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_source(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LanguageSettingsContractTests(unittest.TestCase):
    def test_settings_declare_language_without_private_admin_api(self):
        settings = json.loads((ROOT / "settings/default.json").read_text())
        self.assertEqual(settings["ui"]["language"], "en_US")
        self.assertNotIn("language", settings["hardcoded"])

    def test_tray_loads_settings_locale_not_environment(self):
        with patch.dict(sys.modules, {"tkinter": types.ModuleType("tkinter")}):
            tray = load_source("tray/tray-provider.py", "language1211tray")
        with patch.dict("os.environ", {"NEEBLES_LANGUAGE": "es_CL"}):
            self.assertEqual(tray.load_tray_strings("en_US")["tray.autostart"], "Start Tray with Linux")
            self.assertEqual(tray.load_tray_strings("es_CL")["tray.autostart"], "Iniciar Tray con Linux")

    def test_runtime_string_selection_follows_module_setting(self):
        runtime = load_source("runtime.py", "language1211runtime")
        runtime.CURRENT_LANGUAGE = "en_US"
        self.assertEqual(runtime.strings()["tray.autostart"], "Start Tray with Linux")
        runtime.CURRENT_LANGUAGE = "es_CL"
        self.assertEqual(runtime.strings()["tray.autostart"], "Iniciar Tray con Linux")

    def test_source_includes_live_ui_and_tray_settings_handlers(self):
        ui = (ROOT / "ui/test-module-ui.py").read_text()
        tray = (ROOT / "tray/tray-provider.py").read_text()
        runtime = (ROOT / "runtime.py").read_text()
        self.assertIn('path == "ui.language"', ui)
        self.assertIn('path == "ui.language"', tray)
        self.assertIn('if path == "ui.language"', runtime)
        self.assertIn('"ui.language",', runtime)


if __name__ == "__main__":
    unittest.main()
