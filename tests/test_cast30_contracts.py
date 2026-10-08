"""Guard the N.E.E.B.L.E.S. Test Module 1.2.1 contract without host dependencies."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class TestCast30ModuleContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read_json("manifest.json")
        cls.surfaces = read_json("surfaces.json")
        cls.lifecycle = read_json("lifecycle.json")
        cls.commands = read_json("contracts/commands.json")

    def test_manifest_identity_and_pinned_version(self):
        self.assertEqual(self.manifest["schema"], 4)
        self.assertEqual(self.manifest["name"], "test-module")
        self.assertEqual(self.manifest["version"], "1.2.1")
        self.assertEqual(self.manifest["surfaces"], "surfaces.json")
        self.assertEqual(self.manifest["lifecycle"], "lifecycle.json")
        self.assertEqual(self.manifest["notifications"]["protocol"], 4)
        self.assertEqual(self.manifest["tray"]["construction_step"], "tray-provider")
        self.assertEqual(self.manifest["contracts"][0]["file"], "contracts/commands.json")

    def test_exact_four_surfaces_and_requirements(self):
        self.assertEqual(self.surfaces["schema"], 2)
        items = self.surfaces["items"]
        self.assertEqual(set(items), {
            "open.launcher", "open.tray", "config.notify", "config.notify-switch"
        })
        expected = {
            "open.launcher": ("launcher", "active"),
            "open.tray": ("tray", "active"),
            "config.notify": ("ui", "open"),
            "config.notify-switch": ("ui", "open"),
        }
        for name, (surface, requirement) in expected.items():
            with self.subTest(name=name):
                item = items[name]
                self.assertEqual(item["surface"], surface)
                self.assertIs(item["visible"], True)
                self.assertEqual(item["require"], {"self": requirement, "modules": {}})

    def test_launcher_and_tray_share_one_governed_open(self):
        items = self.surfaces["items"]
        for item_id in ("open.launcher", "open.tray"):
            item = items[item_id]
            self.assertEqual(item["data"]["control"], "button")
            self.assertEqual(item["data"]["action"], "open")
            self.assertEqual(item["data"]["label_key"], "surface.open")
        self.assertEqual(self.lifecycle["hardcoded"]["governor.open"], "open")
        open_ops = self.lifecycle["transitions"]["open"]["operations"]
        self.assertEqual(len(open_ops), 1)
        operation = next(iter(open_ops.values()))
        self.assertEqual(operation["artillery"], "boss.workspace_execution")
        self.assertEqual(operation["objective"], "construction.step")
        self.assertEqual(operation["munition"], {"step": "open-runtime"})

    def test_notification_surface_uses_governed_module_ipc(self):
        item = self.surfaces["items"]["config.notify"]
        self.assertEqual(item["data"]["control"], "button")
        self.assertEqual(item["data"]["action"], "notify-demo")
        self.assertEqual(self.lifecycle["hardcoded"]["governor.notify-demo"], "notify-demo")
        op = self.lifecycle["transitions"]["notify-demo"]["operations"]["notify"]
        self.assertEqual(op["artillery"], "boss.module_ipc")
        self.assertEqual(op["objective"], "commands")
        self.assertEqual(op["munition"], {"endpoint": "notify"})
        self.assertEqual(self.commands["endpoints"]["notify"]["endpoint"], "test.notify")

    def test_switch_requires_live_runtime_and_has_object_transitions(self):
        item = self.surfaces["items"]["config.notify-switch"]
        self.assertEqual(item["object_id"], "notify-switch")
        self.assertEqual(item["data"]["control"], "switch")
        obj = self.lifecycle["objects"]["notify-switch"]
        self.assertIs(obj["initial_active"], False)
        for direction, value in (("on", True), ("off", False)):
            with self.subTest(direction=direction):
                action = "feature-" + direction
                self.assertEqual(item["data"]["action_" + direction], action)
                self.assertEqual(item["data"]["transition_" + direction], action)
                self.assertIs(obj["transition_active"][action], value)
                op = obj["transitions"][action]["operations"]["notify"]
                self.assertEqual(op["artillery"], "boss.module_ipc")
                self.assertEqual(op["munition"], {"endpoint": "notify"})

    def test_presentations_have_both_languages(self):
        keys = {item["data"]["label_key"] for item in self.surfaces["items"].values()}
        self.assertEqual(keys, {"surface.open", "features.notify", "features.notify_switch"})
        for code in ("en_US", "es_CL"):
            with self.subTest(locale=code):
                strings = read_json("languages/" + code + ".json")
                for key in keys:
                    self.assertTrue(isinstance(strings.get(key), str) and strings[key].strip())

    def test_runtime_and_ui_python_parse_without_importing_tk(self):
        for rel in ("runtime.py", "tray/tray-provider.py", "ui/test-module-ui.py"):
            with self.subTest(path=rel):
                source = (ROOT / rel).read_text(encoding="utf-8")
                ast.parse(source, filename=rel)

    def test_documentation_matches_surface_requirements(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Current module version:\n\n```text\n1.2.1\n```", readme)
        subsection = readme.split("# 16. Surfaces", 1)[1].split("# 17. UI", 1)[0]
        self.assertEqual(subsection.count("-> require self active"), 2)
        self.assertEqual(subsection.count("-> require self open"), 2)


if __name__ == "__main__":
    unittest.main()
