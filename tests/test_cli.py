import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "lib"))

from aegis_maintenance.detect import SystemDetector
from aegis_maintenance.backends.registry import BackendRegistry
from aegis_maintenance.reporting import render_report


import unittest


class TestAegisMaintenance(unittest.TestCase):
    def test_os_release_detection(self):
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tempdir:
            sample = Path(tempdir) / "os-release"
            sample.write_text('''ID=gentoo
NAME="Gentoo Linux"
VERSION_ID="2026.0"
''')
            detector = SystemDetector()
            detector.OS_RELEASE_PATH = str(sample)
            context = detector.detect()

            self.assertEqual(context.distribution_id, "gentoo")
            self.assertEqual(context.distribution_name, "Gentoo Linux")
            self.assertEqual(context.version_id, "2026.0")

    def test_backend_selection_gentoo(self):
        class FakeContext:
            distribution_id = "gentoo"
            os_release = {}

        backend = BackendRegistry().select_backend(FakeContext())
        self.assertEqual(backend.identifier, "gentoo")

    def test_render_report_json(self):
        report = {
            "id": "test-report",
            "backend": "fake",
            "distribution": "gentoo",
            "command": "check",
            "status": "SUCCESS",
            "diagnostics": {},
            "actions": {},
        }
        output = render_report(report, fmt="json")
        self.assertIn('"id": "test-report"', output)


if __name__ == "__main__":
    unittest.main()
