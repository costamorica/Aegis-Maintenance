import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "lib"))

from aegis_maintenance.backends.gentoo import GentooBackend
from aegis_maintenance.backends.registry import BackendRegistry
from aegis_maintenance.cli import _exit_code
from aegis_maintenance.detect import SystemDetector
from aegis_maintenance.domain.context import ExecutionContext
from aegis_maintenance.execution import CommandResult
from aegis_maintenance.diagnostics import DiagnosticLevel


class TestBackendAndRegistry(unittest.TestCase):
    def test_endeavouros_selected_before_arch_by_id_like(self):
        class FakeContext:
            distribution_id = None
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = BackendRegistry().select_backend(FakeContext())
        self.assertIsNotNone(backend)
        self.assertEqual("endeavouros", backend.identifier)

    def test_unsupported_distribution_is_rejected(self):
        class FakeContext:
            distribution_id = "fedora"
            os_release = {"ID": "fedora", "ID_LIKE": "fedora"}

        backend = BackendRegistry().select_backend(FakeContext())
        self.assertIsNone(backend)

        report = ExecutionContext(FakeContext(), backend).execute("check")
        self.assertEqual("BLOCKED", report.status)
        self.assertEqual("unsupported", report.backend)
        self.assertEqual("unsupported-distribution", report.diagnostics[0]["id"])

    def test_os_release_absent_returns_empty_fields(self):
        with tempfile.TemporaryDirectory() as tempdir:
            sample = Path(tempdir) / "os-release"
            sample.write_text("")
            detector = SystemDetector()
            detector.OS_RELEASE_PATH = str(sample)
            context = detector.detect()

            self.assertIsNone(context.distribution_id)
            self.assertEqual([], context.id_like)
            self.assertEqual({}, context.os_release)

    def test_gentoo_emerge_missing_returns_failed(self):
        class FakeContext:
            distribution_id = "gentoo"
            os_release = {}

        backend = GentooBackend()
        with patch.object(backend.executor, "which", return_value=None):
            report = backend.check(FakeContext())

        self.assertEqual("FAILED", report.status)
        self.assertEqual("ERROR", report.diagnostics[0]["level"])
        self.assertEqual("emerge-missing", report.diagnostics[0]["id"])

    def test_gentoo_world_plan_no_candidates_is_success(self):
        class FakeContext:
            distribution_id = "gentoo"
            os_release = {}

        backend = GentooBackend()
        result = CommandResult(
            command=["emerge"],
            returncode=0,
            stdout="No packages to merge.",
            stderr="",
        )
        with patch.object(backend.executor, "which", return_value="/usr/bin/emerge"), patch.object(backend.executor, "run", return_value=result):
            report = backend.check(FakeContext())

        self.assertEqual("SUCCESS", report.status)
        self.assertEqual("OK", report.diagnostics[0]["level"])
        self.assertIn("No packages were selected for update", report.diagnostics[0]["detail"])

    def test_gentoo_world_plan_with_candidates_is_notice(self):
        class FakeContext:
            distribution_id = "gentoo"
            os_release = {}

        backend = GentooBackend()
        result = CommandResult(
            command=["emerge"],
            returncode=0,
            stdout="[ebuild] sys-apps/portage-3.0.9::gentoo \n * USE='bindist -test'",
            stderr="",
        )
        with patch.object(backend.executor, "which", return_value="/usr/bin/emerge"), patch.object(backend.executor, "run", return_value=result):
            report = backend.check(FakeContext())

        self.assertEqual("SUCCESS_WITH_NOTICES", report.status)
        self.assertEqual("NOTICE", report.diagnostics[0]["level"])
        self.assertIn("[ebuild] sys-apps/portage-3.0.9::gentoo", report.diagnostics[0]["detail"])

    def test_cli_exit_code_mapping(self):
        self.assertEqual(0, _exit_code("SUCCESS"))
        self.assertEqual(1, _exit_code("SUCCESS_WITH_NOTICES"))
        self.assertEqual(2, _exit_code("ACTION_REQUIRED"))
        self.assertEqual(2, _exit_code("BLOCKED"))
        self.assertEqual(3, _exit_code("FAILED"))
        self.assertEqual(4, _exit_code("UNKNOWN"))


if __name__ == "__main__":
    unittest.main()
