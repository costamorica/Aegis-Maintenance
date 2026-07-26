from typing import Dict

from aegis_maintenance.backends.arch import ArchBackend
from aegis_maintenance.backends.endeavouros import EndeavourOSBackend
from aegis_maintenance.backends.gentoo import GentooBackend
from aegis_maintenance.backends.base import Backend


class BackendRegistry:
    def __init__(self):
        self._backends: Dict[str, Backend] = {}
        self.register_backend(GentooBackend())
        self.register_backend(ArchBackend())
        self.register_backend(EndeavourOSBackend())

    def register_backend(self, backend: Backend):
        self._backends[backend.identifier] = backend

    def select_backend(self, system_context):
        distribution_id = (system_context.distribution_id or "").strip().lower()
        if distribution_id in self._backends:
            return self._backends[distribution_id]

        os_release = getattr(system_context, "os_release", {}) or {}
        id_like = os_release.get("ID_LIKE", "").lower()
        if "gentoo" in id_like and "gentoo" in self._backends:
            return self._backends["gentoo"]
        if "endeavouros" in id_like and "endeavouros" in self._backends:
            return self._backends["endeavouros"]
        if "arch" in id_like and "arch" in self._backends:
            return self._backends["arch"]

        return self._backends.get("arch", next(iter(self._backends.values())))
