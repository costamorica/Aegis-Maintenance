from datetime import datetime, timezone
from typing import Dict

from aegis_maintenance.domain.plan import ExecutionPlan
from aegis_maintenance.domain.report import Report


class UpdateWorkflow:
    def __init__(self, plan: ExecutionPlan, interactive: bool = False):
        self.plan = plan
        self.interactive = interactive

    def run(self) -> Report:
        diagnostics = list(self.plan.diagnostics)
        actions = list(self.plan.actions) if self.plan.actions else []
        actions.append({"note": "Dry run update plan generated."})

        if self.plan.package_changes:
            diagnostics.append(
                {
                    "id": "update-plan-summary",
                    "level": "NOTICE",
                    "title": "Update plan ready",
                    "detail": f"{len(self.plan.package_changes)} package(s) will be updated.",
                    "data": {"package_changes": self.plan.package_changes},
                }
            )
        else:
            diagnostics.append(
                {
                    "id": "update-plan-none",
                    "level": "OK",
                    "title": "No package updates are currently available",
                    "detail": "No package changes were detected.",
                    "data": {},
                }
            )

        status = self._status_from_diagnostics(diagnostics)
        metadata = dict(self.plan.metadata)
        metadata.update(
            {
                "dry_run": True,
                "workflow": "update",
                "plan_mode": "dry_run",
                "package_changes_count": len(self.plan.package_changes),
            }
        )

        return Report(
            id=f"{self.plan.backend}-{self.plan.command}-{self._timestamp()}",
            timestamp=self._now(),
            backend=self.plan.backend,
            distribution=self.plan.distribution,
            command=self.plan.command,
            status=status,
            diagnostics=diagnostics,
            actions=actions,
            metadata=metadata,
        )

    def _status_from_diagnostics(self, diagnostics: list[Dict[str, str]]) -> str:
        levels = {diag.get("level") for diag in diagnostics}
        if "CRITICAL" in levels or "ERROR" in levels:
            return "FAILED"
        if "WARNING" in levels or "NOTICE" in levels:
            return "SUCCESS_WITH_NOTICES"
        if "OK" in levels or "INFO" in levels:
            return "SUCCESS"
        return "UNKNOWN"

    def _now(self):
        return datetime.now(timezone.utc)

    def _timestamp(self) -> str:
        return self._now().strftime("%Y%m%d%H%M%S")
