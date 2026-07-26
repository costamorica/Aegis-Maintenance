from typing import Any

from aegis_maintenance.diagnostics import Diagnostic, DiagnosticLevel
from aegis_maintenance.domain.report import Report
from aegis_maintenance.workflow import UpdateWorkflow


class ExecutionContext:
    def __init__(self, system_context: Any, backend: Any):
        self.system_context = system_context
        self.backend = backend

    def execute(self, command: str) -> Report:
        if self.backend is None:
            return self._unsupported_distribution_report(command)

        if command == "check":
            return self.backend.check(self.system_context)
        if command == "update":
            plan = self.backend.prepare_update_plan(self.system_context)
            return UpdateWorkflow(plan).run()
        if command == "clean":
            return self.backend.clean(self.system_context)
        if command == "report":
            return self.backend.report(self.system_context)
        if command == "doctor":
            return self.backend.doctor(self.system_context)
        raise ValueError(f"Commande inconnue: {command}")

    def _unsupported_distribution_report(self, command: str) -> Report:
        distribution = getattr(self.system_context, "distribution_id", "unknown") or "unknown"
        diagnostics = [
            Diagnostic(
                id="unsupported-distribution",
                level=DiagnosticLevel.WARNING,
                title="Distribution non prise en charge",
                detail=f"Aucune implémentation backend pour la distribution '{distribution}'.",
            ).to_dict()
        ]
        return Report(
            id=f"unsupported-{command}",
            timestamp=self._now(),
            backend="unsupported",
            distribution=distribution,
            command=command,
            status="BLOCKED",
            diagnostics=diagnostics,
            actions=[],
            metadata={"reason": "unsupported distribution"},
        )

    def _now(self):
        from datetime import datetime, timezone

        return datetime.now(timezone.utc)
