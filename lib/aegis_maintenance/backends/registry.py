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

        matched = [backend for backend in self._backends.values() if backend.matches(system_context)]
        if not matched:
            return None
        return max(matched, key=lambda backend: backend.priority)
