"""Test Module 1.2.8: declarative Uninstall checklist contract sanity tests.

These tests do NOT certify the Boss Rust executor or a real systemd session.
"""
import json
import unittest
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / 'manifest.json'


class UninstallContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        cls.contract = cls.manifest['uninstall']

    def test_manifest_version_does_not_regress(self):
        self.assertEqual(self.manifest['version'], '1.2.9')
        self.assertEqual(self.manifest['schema'], 4)

    def test_governor_remains_main(self):
        self.assertEqual(self.contract['main'], 'governor')
        self.assertEqual(self.contract['schema'], 1)
        self.assertEqual(self.manifest['entrypoint'], 'runtime.py')

    def test_tray_reuses_managed_manifest_reference(self):
        tray = next(item for item in self.contract['extras'] if item['id'] == 'tray')
        self.assertEqual((tray['type'], tray['ref']), ('governed', 'manifest.tray'))
        self.assertTrue(self.manifest.get('tray'))

    def test_service_owned_by_module(self):
        service = next(item for item in self.contract['extras'] if item['id'] == 'session-controller')
        name = service['name'].replace('$hardcoded.session_service', self.contract['hardcoded']['session_service'])
        self.assertTrue(name.startswith('neebles-test-module-'))
        self.assertTrue(name.endswith('.service'))
        self.assertEqual(service['provider'], 'systemd-user')
        self.assertTrue(service['stop']['disable'])
        self.assertTrue(service['remove'])

    def test_cleanup_preserves_user_settings_choice(self):
        state = next(item for item in self.contract['cleanup'] if item['type'] == 'settings')
        self.assertEqual((state['ref'], state['policy']), ('manifest.settings', 'user-choice'))
        self.assertTrue(all(value == 'abort' for value in self.contract['failure'].values()))


if __name__ == '__main__':
    unittest.main()
