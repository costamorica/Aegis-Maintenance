from typing import Any

from aegis_maintenance.domain.report import Report


class ExecutionContext:
    def __init__(self, system_context: Any, backend: Any):
        self.system_context = system_context
        self.backend = backend

    def execute(self, command: str) -> Report:
        if command == "check":
            return self.backend.check(self.system_context)
        if command == "update":
            return self.backend.update(self.system_context)
        if command == "clean":
            return self.backend.clean(self.system_context)
        if command == "report":
            return self.backend.report(self.system_context)
        if command == "doctor":
            return self.backend.doctor(self.system_context)
        raise ValueError(f"Commande inconnue: {command}")
