import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG = ROOT / "languages"

class MultilingualCatalogTests(unittest.TestCase):
    def test_catalog_and_full_translation_key_parity(self):
        manifest = json.loads((LANG / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], 1)
        self.assertEqual(manifest["default"], "en_US")
        self.assertEqual(len(manifest["languages"]), 253)
        original = json.loads((LANG / "en_US.json").read_text(encoding="utf-8"))
        expected = set(original)
        self.assertEqual(len(expected), 32)
        codes = set()
        files = set()
        for locale in manifest["languages"]:
            code, filename = locale["code"], locale["file"]
            self.assertNotIn(code, codes)
            self.assertNotIn(filename, files)
            codes.add(code)
            files.add(filename)
            self.assertEqual(filename, code + ".json")
            data = json.loads((LANG / filename).read_text(encoding="utf-8"))
            self.assertEqual(set(data), expected, code)
            self.assertTrue(all(isinstance(value, str) for value in data.values()), code)
        actual = {path.name for path in LANG.glob("*.json")} - {"manifest.json"}
        self.assertEqual(actual, files)
        self.assertIn("es_CL", codes)
        self.assertIn("en_US", codes)

    def test_module_version(self):
        version = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]
        self.assertEqual(version, "1.2.12")

if __name__ == "__main__":
    unittest.main()
