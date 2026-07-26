from datetime import datetime, timezone
from typing import Dict, List

from aegis_maintenance.domain.plan import ExecutionAction, ExecutionPlan
from aegis_maintenance.domain.report import Report


class UpdatePlanningWorkflow:
    def __init__(self, plan: ExecutionPlan, interactive: bool = False):
        self.plan = plan
        self.interactive = interactive

    def prepare(self) -> ExecutionPlan:
        return self.plan

    def validate_plan(self) -> None:
        if self.plan is None:
            raise ValueError("Execution plan is required")

    def execute_plan(self) -> None:
        if not self.plan.dry_run:
            raise NotImplementedError("Plan execution is not implemented yet")

    def run(self) -> Report:
        self.validate_plan()
        plan = self.prepare()
        return self.build_report(plan)

    def build_report(self, plan: ExecutionPlan) -> Report:
        diagnostics = list(plan.diagnostics)
        actions = [action.to_dict() for action in plan.actions]
        actions.append(
            ExecutionAction(
                id="dry-run-plan-generated",
                description="Dry run update plan generated.",
                needs_sudo=False,
            ).to_dict()
        )

        if plan.package_changes:
            diagnostics.append(
                {
                    "id": "update-plan-summary",
                    "level": "NOTICE",
                    "title": "Update plan ready",
                    "detail": f"{len(plan.package_changes)} package(s) will be updated.",
                    "data": {"package_changes": plan.package_changes},
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
        metadata = dict(plan.metadata)
        metadata.update(
            {
                "dry_run": plan.dry_run,
                "workflow": "update",
                "plan_mode": "dry_run",
                "package_changes_count": len(plan.package_changes),
            }
        )

        return Report(
            id=f"{plan.backend}-{plan.command}-{self._timestamp()}",
            timestamp=self._now(),
            backend=plan.backend,
            distribution=plan.distribution,
            command=plan.command,
            status=status,
            diagnostics=diagnostics,
            actions=actions,
            metadata=metadata,
        )

    def _status_from_diagnostics(self, diagnostics: List[Dict[str, str]]) -> str:
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
