import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "lib"))

from aegis_maintenance.detect import SystemDetector
from aegis_maintenance.backends.registry import BackendRegistry
from aegis_maintenance.reporting import render_report


def test_arch_backend_render_json():
    class FakeContext:
        distribution_id = "arch"
        os_release = {"ID_LIKE": "arch"}

    backend = BackendRegistry().select_backend(FakeContext())
    report = backend.check(FakeContext())
    output = render_report(report, fmt="json")

    assert '"backend": "arch"' in output
    assert '"metadata"' in output


def test_gentoo_backend_selection():
    class FakeContext:
        distribution_id = "gentoo"
        os_release = {"ID_LIKE": "gentoo"}

    backend = BackendRegistry().select_backend(FakeContext())
    assert backend.identifier == "gentoo"
