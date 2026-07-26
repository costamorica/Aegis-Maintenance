import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "lib"))

from aegis_maintenance.backends.gentoo import GentooBackend
from aegis_maintenance.backends.endeavouros import EndeavourOSBackend
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

    def test_endeavouros_orphans_return_code_one_is_success(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        result = CommandResult(
            command=["pacman", "-Qdtq"],
            returncode=1,
            stdout="",
            stderr="",
        )
        with patch.object(backend.executor, "run", side_effect=[
            CommandResult(command=["bash", "-lc", "grep -E '^\\[endeavouros\\]' /etc/pacman.conf 2>/dev/null | head -n 1"], returncode=0, stdout="[endeavouros]", stderr=""),
            CommandResult(command=["checkupdates"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Dk"], returncode=0, stdout="", stderr=""),
            result,
            CommandResult(command=["pacman", "-Qm"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "du -sh /var/cache/pacman/pkg 2>/dev/null || true"], returncode=0, stdout="100M\t/var/cache/pacman/pkg", stderr=""),
            CommandResult(command=["systemctl", "list-units", "--state=failed", "--no-pager", "--no-legend"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "findmnt -n -o SOURCE,TARGET / | tr -s ' '"], returncode=0, stdout="/dev/nvme0n1p2 /", stderr=""),
            CommandResult(command=["df", "-h", "/"], returncode=0, stdout="Filesystem Size Used Avail Use% Mounted on\n/dev/nvme0n1p2 100G 50G 50G 50% /", stderr=""),
            CommandResult(command=["bash", "-lc", "[ -f /var/run/reboot-required ] && echo reboot-required || true"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacsave' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacnew' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
        ]):
            report = backend.check(FakeContext())

        self.assertEqual("SUCCESS", report.status)
        orphans = next(d for d in report.diagnostics if d["id"] == "orphans-none")
        self.assertEqual("OK", orphans["level"])

    def test_endeavouros_orphans_found_is_notice(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        result = CommandResult(
            command=["pacman", "-Qdtq"],
            returncode=0,
            stdout="bats\nlibayatana-appindicator\nllvm\nopenmp",
            stderr="",
        )
        with patch.object(backend.executor, "run", side_effect=[
            CommandResult(command=["bash", "-lc", "grep -E '^\\[endeavouros\\]' /etc/pacman.conf 2>/dev/null | head -n 1"], returncode=0, stdout="[endeavouros]", stderr=""),
            CommandResult(command=["checkupdates"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Dk"], returncode=0, stdout="", stderr=""),
            result,
            CommandResult(command=["pacman", "-Qm"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "du -sh /var/cache/pacman/pkg 2>/dev/null || true"], returncode=0, stdout="100M\t/var/cache/pacman/pkg", stderr=""),
            CommandResult(command=["systemctl", "list-units", "--state=failed", "--no-pager", "--no-legend"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "findmnt -n -o SOURCE,TARGET / | tr -s ' '"], returncode=0, stdout="/dev/nvme0n1p2 /", stderr=""),
            CommandResult(command=["df", "-h", "/"], returncode=0, stdout="Filesystem Size Used Avail Use% Mounted on\n/dev/nvme0n1p2 100G 50G 50G 50% /", stderr=""),
            CommandResult(command=["bash", "-lc", "[ -f /var/run/reboot-required ] && echo reboot-required || true"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacsave' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacnew' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
        ]):
            report = backend.check(FakeContext())

        self.assertEqual("SUCCESS_WITH_NOTICES", report.status)
        orphans = next(d for d in report.diagnostics if d["id"] == "orphans-found")
        self.assertEqual("NOTICE", orphans["level"])

    def test_endeavouros_foreign_packages_found_is_notice(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        result = CommandResult(
            command=["pacman", "-Qm"],
            returncode=0,
            stdout="arch-update\narduino-ide-bin\nicu69\nkdrive-bin\nobsidian-bin\nshelly\nventoy-bin\nvisual-studio-code-bin",
            stderr="",
        )
        with patch.object(backend.executor, "run", side_effect=[
            CommandResult(command=["bash", "-lc", "grep -E '^\\[endeavouros\\]' /etc/pacman.conf 2>/dev/null | head -n 1"], returncode=0, stdout="[endeavouros]", stderr=""),
            CommandResult(command=["checkupdates"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Dk"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Qdtq"], returncode=1, stdout="", stderr=""),
            result,
            CommandResult(command=["bash", "-lc", "du -sh /var/cache/pacman/pkg 2>/dev/null || true"], returncode=0, stdout="100M\t/var/cache/pacman/pkg", stderr=""),
            CommandResult(command=["systemctl", "list-units", "--state=failed", "--no-pager", "--no-legend"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "findmnt -n -o SOURCE,TARGET / | tr -s ' '"], returncode=0, stdout="/dev/nvme0n1p2 /", stderr=""),
            CommandResult(command=["df", "-h", "/"], returncode=0, stdout="Filesystem Size Used Avail Use% Mounted on\n/dev/nvme0n1p2 100G 50G 50G 50% /", stderr=""),
            CommandResult(command=["bash", "-lc", "[ -f /var/run/reboot-required ] && echo reboot-required || true"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacsave' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacnew' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
        ]):
            report = backend.check(FakeContext())

        self.assertEqual("SUCCESS_WITH_NOTICES", report.status)
        foreign_packages = next(d for d in report.diagnostics if d["id"] == "foreign-packages-found")
        self.assertEqual("NOTICE", foreign_packages["level"])

    def test_endeavouros_update_plan_reports_read_only(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        result = CommandResult(
            command=["pacman", "-Qu"],
            returncode=0,
            stdout="pkgconf 3.0.3-1 -> 3.0.4-1",
            stderr="",
        )
        with patch.object(backend.executor, "which", return_value=None), patch.object(backend.executor, "run", return_value=result):
            report = backend.update(FakeContext())

        self.assertEqual("SUCCESS_WITH_NOTICES", report.status)
        self.assertEqual("update-plan-available", report.diagnostics[0]["id"])
        self.assertEqual("update-plan-summary", report.diagnostics[1]["id"])
        self.assertIn("read-only", report.diagnostics[1]["detail"])
        self.assertEqual("Mode: update plan; Changes performed: none.", report.actions[0]["note"])

    def test_execution_context_update_runs_update_workflow(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        result = CommandResult(
            command=["pacman", "-Qu"],
            returncode=0,
            stdout="pkgconf 3.0.3-1 -> 3.0.4-1",
            stderr="",
        )

        with patch.object(backend.executor, "which", return_value=None), patch.object(backend.executor, "run", return_value=result):
            report = ExecutionContext(FakeContext(), backend).execute("update")

        self.assertEqual("SUCCESS_WITH_NOTICES", report.status)
        self.assertEqual("update-plan-available", report.diagnostics[0]["id"])
        self.assertEqual("update-plan-summary", report.diagnostics[-1]["id"])
        self.assertGreaterEqual(len(report.actions), 1)
        self.assertIn("Dry run update plan generated", report.actions[-1]["note"])

    def test_prepare_update_plan_includes_package_changes(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        result = CommandResult(
            command=["pacman", "-Qu"],
            returncode=0,
            stdout="pkgconf 3.0.3-1 -> 3.0.4-1\npython-3.12.0-1 -> 3.12.1-1",
            stderr="",
        )

        with patch.object(backend.executor, "which", return_value=None), patch.object(backend.executor, "run", return_value=result):
            plan = backend.prepare_update_plan(FakeContext())

        self.assertEqual("endeavouros", plan.backend)
        self.assertEqual("update", plan.command)
        self.assertEqual(2, len(plan.package_changes))
        self.assertIn("pkgconf 3.0.3-1 -> 3.0.4-1", plan.package_changes)
        self.assertTrue(plan.needs_confirmation)
        self.assertTrue(plan.needs_sudo)

    def test_endeavouros_update_plan_none_is_ok(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        result = CommandResult(
            command=["pacman", "-Qu"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with patch.object(backend.executor, "which", return_value=None), patch.object(backend.executor, "run", return_value=result):
            report = backend.update(FakeContext())

        self.assertEqual("SUCCESS", report.status)
        self.assertEqual("update-plan-none", report.diagnostics[0]["id"])
        self.assertEqual("OK", report.diagnostics[0]["level"])
        self.assertEqual("update-plan-summary", report.diagnostics[1]["id"])

    def test_endeavouros_checkupdates_failure_reports_warning(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        result = CommandResult(
            command=["checkupdates"],
            returncode=1,
            stdout="",
            stderr="error: failed to contact update server",
        )
        with patch.object(backend.executor, "which", return_value="checkupdates"), patch.object(backend.executor, "run", return_value=result):
            report = backend.update(FakeContext())

        self.assertEqual("SUCCESS_WITH_NOTICES", report.status)
        self.assertEqual("update-plan-failed", report.diagnostics[0]["id"])
        self.assertEqual("WARNING", report.diagnostics[0]["level"])

    def test_endeavouros_cache_detected_is_info(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        with patch.object(backend.executor, "run", side_effect=[
            CommandResult(command=["bash", "-lc", "grep -E '^\\[endeavouros\\]' /etc/pacman.conf 2>/dev/null | head -n 1"], returncode=0, stdout="[endeavouros]", stderr=""),
            CommandResult(command=["checkupdates"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Dk"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Qdtq"], returncode=1, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Qm"], returncode=1, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "du -sh /var/cache/pacman/pkg 2>/dev/null || true"], returncode=0, stdout="1.2G\t/var/cache/pacman/pkg", stderr=""),
            CommandResult(command=["systemctl", "list-units", "--state=failed", "--no-pager", "--no-legend"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "findmnt -n -o SOURCE,TARGET / | tr -s ' '"], returncode=0, stdout="/dev/nvme0n1p2 /", stderr=""),
            CommandResult(command=["df", "-h", "/"], returncode=0, stdout="Filesystem Size Used Avail Use% Mounted on\n/dev/nvme0n1p2 100G 60G 40G 60% /", stderr=""),
            CommandResult(command=["bash", "-lc", "[ -f /var/run/reboot-required ] && echo reboot-required || true"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacsave' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacnew' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
        ]):
            report = backend.check(FakeContext())

        cache = next(d for d in report.diagnostics if d["id"] == "pacman-cache-size")
        self.assertEqual("INFO", cache["level"])
        self.assertIn("1.2G", cache["detail"])

    def test_endeavouros_systemd_failed_services_warning(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        with patch.object(backend.executor, "run", side_effect=[
            CommandResult(command=["bash", "-lc", "grep -E '^\\[endeavouros\\]' /etc/pacman.conf 2>/dev/null | head -n 1"], returncode=0, stdout="[endeavouros]", stderr=""),
            CommandResult(command=["checkupdates"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Dk"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Qdtq"], returncode=1, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Qm"], returncode=1, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "du -sh /var/cache/pacman/pkg 2>/dev/null || true"], returncode=0, stdout="100M\t/var/cache/pacman/pkg", stderr=""),
            CommandResult(command=["systemctl", "list-units", "--state=failed", "--no-pager", "--no-legend"], returncode=0, stdout="foo.service loaded failed failed Foo Service", stderr=""),
            CommandResult(command=["bash", "-lc", "findmnt -n -o SOURCE,TARGET / | tr -s ' '"], returncode=0, stdout="/dev/nvme0n1p2 /", stderr=""),
            CommandResult(command=["df", "-h", "/"], returncode=0, stdout="Filesystem Size Used Avail Use% Mounted on\n/dev/nvme0n1p2 100G 70G 30G 70% /", stderr=""),
            CommandResult(command=["bash", "-lc", "[ -f /var/run/reboot-required ] && echo reboot-required || true"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacsave' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacnew' 2>/dev/null | head -n 20"], returncode=0, stdout="", stderr=""),
        ]):
            report = backend.check(FakeContext())

        failed = next(d for d in report.diagnostics if d["id"] == "systemd-failed-services")
        self.assertEqual("WARNING", failed["level"])
        self.assertIn("foo.service", failed["detail"])

    def test_endeavouros_pacnew_and_pacsave_present(self):
        class FakeContext:
            distribution_id = "endeavouros"
            os_release = {"ID_LIKE": "arch endeavouros"}

        backend = EndeavourOSBackend()
        with patch.object(backend.executor, "run", side_effect=[
            CommandResult(command=["bash", "-lc", "grep -E '^\\[endeavouros\\]' /etc/pacman.conf 2>/dev/null | head -n 1"], returncode=0, stdout="[endeavouros]", stderr=""),
            CommandResult(command=["checkupdates"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Dk"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Qdtq"], returncode=1, stdout="", stderr=""),
            CommandResult(command=["pacman", "-Qm"], returncode=1, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "du -sh /var/cache/pacman/pkg 2>/dev/null || true"], returncode=0, stdout="100M\t/var/cache/pacman/pkg", stderr=""),
            CommandResult(command=["systemctl", "list-units", "--state=failed", "--no-pager", "--no-legend"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "findmnt -n -o SOURCE,TARGET / | tr -s ' '"], returncode=0, stdout="/dev/nvme0n1p2 /", stderr=""),
            CommandResult(command=["df", "-h", "/"], returncode=0, stdout="Filesystem Size Used Avail Use% Mounted on\n/dev/nvme0n1p2 100G 60G 40G 60% /", stderr=""),
            CommandResult(command=["bash", "-lc", "[ -f /var/run/reboot-required ] && echo reboot-required || true"], returncode=0, stdout="", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacsave' 2>/dev/null | head -n 20"], returncode=0, stdout="/etc/example.pacsave", stderr=""),
            CommandResult(command=["bash", "-lc", "find /etc -name '*.pacnew' 2>/dev/null | head -n 20"], returncode=0, stdout="/etc/example.pacnew", stderr=""),
        ]):
            report = backend.check(FakeContext())

        pacsave = next(d for d in report.diagnostics if d["id"] == "pacsave-files")
        pacnew = next(d for d in report.diagnostics if d["id"] == "pacnew-files")
        self.assertEqual("NOTICE", pacsave["level"])
        self.assertEqual("NOTICE", pacnew["level"])

    def test_cli_exit_code_mapping(self):
        self.assertEqual(0, _exit_code("SUCCESS"))
        self.assertEqual(1, _exit_code("SUCCESS_WITH_NOTICES"))
        self.assertEqual(2, _exit_code("ACTION_REQUIRED"))
        self.assertEqual(2, _exit_code("BLOCKED"))
        self.assertEqual(3, _exit_code("FAILED"))
        self.assertEqual(4, _exit_code("UNKNOWN"))


if __name__ == "__main__":
    unittest.main()
