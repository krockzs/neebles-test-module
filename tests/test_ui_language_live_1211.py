"""Regression: Tk UI must relabel existing widgets when Settings emits ui.language.

The fake Tk geometry manager deliberately returns None, as real Tk does.
No X server, Boss IPC, process service, or installed module is required.
"""

import io
import json
import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class FakeWidget:
    def __init__(self, *args, **kwargs):
        self.options = dict(kwargs)
        self.title_value = ""
        self.scheduled = []

    def pack(self, *args, **kwargs):
        return None  # Tk geometry managers do not return the widget.

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def title(self, value):
        self.title_value = value

    def geometry(self, *args):
        pass

    def minsize(self, *args):
        pass

    def after(self, delay, callback):
        self.scheduled.append((delay, callback))

    def mainloop(self):
        pass

    def delete(self, *args):
        pass

    def insert(self, *args):
        pass


class FakeBooleanVar:
    def __init__(self, value=False):
        self.value = bool(value)

    def get(self):
        return self.value

    def set(self, value):
        self.value = bool(value)


def fake_tkinter():
    module = types.ModuleType("tkinter")
    for widget in ("Tk", "Label", "Text", "LabelFrame", "Checkbutton", "Frame", "Button"):
        setattr(module, widget, FakeWidget)
    module.BooleanVar = FakeBooleanVar
    return module


def instantiate_ui():
    with patch.dict(sys.modules, {"tkinter": fake_tkinter()}), \
         patch.object(sys, "stdin", io.StringIO("")), \
         patch.object(sys, "stdout", io.StringIO()):
        return runpy.run_path(str(ROOT / "ui/test-module-ui.py"))


class LiveTkLanguageTests(unittest.TestCase):
    def test_live_language_controls_keep_widget_references(self):
        ui = instantiate_ui()
        for field in ("option1_control", "option2_control", "tray_visible_control", "tray_autostart_control"):
            with self.subTest(field=field):
                self.assertIsInstance(ui[field], FakeWidget, f"{field} lost its widget reference")

    def test_runtime_settings_event_relabels_same_tk_widgets(self):
        ui = instantiate_ui()
        option1 = ui["option1_control"]
        self.assertEqual(option1.options["text"], "Feature Option 1")
        ui["RUNTIME_EVENTS"].put({"type": "settings_changed", "path": "ui.language", "value": "es_CL"})
        ui["RUNTIME_EVENTS"].put({"type": "settings_changed", "path": "features.option1", "value": "true"})
        ui["drain_runtime_events"]()
        self.assertIs(option1, ui["option1_control"])
        self.assertEqual(option1.options["text"], "Función de prueba 1")
        self.assertEqual(ui["tray_visible_control"].options["text"], "Mostrar Tray")
        self.assertTrue(ui["option1"].get())
        ui["RUNTIME_EVENTS"].put({"type": "settings_changed", "path": "ui.language", "value": "en_US"})
        ui["drain_runtime_events"]()
        self.assertEqual(option1.options["text"], "Feature Option 1")

    def test_module_language_fallback_matches_settings_default(self):
        language_manifest = json.loads((ROOT / "languages/manifest.json").read_text(encoding="utf-8"))
        settings = json.loads((ROOT / "settings/default.json").read_text(encoding="utf-8"))
        self.assertEqual(language_manifest["default"], settings["ui"]["language"])


if __name__ == "__main__":
    unittest.main()
