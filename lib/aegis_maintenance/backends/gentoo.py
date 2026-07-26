from typing import Any, Dict, List, Optional

from aegis_maintenance.backends.base import Backend
from aegis_maintenance.diagnostics import DiagnosticLevel


class GentooBackend(Backend):
    identifier = "gentoo"
    priority = 20
    supported_distributions = ("gentoo",)
    family = "gentoo"

    def matches(self, system_context: Any) -> bool:
        distribution = (getattr(system_context, "distribution_id", None) or "").lower()
        os_release = getattr(system_context, "os_release", {}) or {}
        id_like = os_release.get("ID_LIKE", "").lower()
        return distribution == "gentoo" or "gentoo" in id_like

    def check(self, system_context: Any):
        diagnostics: List[Dict[str, Any]] = []

        if not self.executor.which("emerge"):
            diagnostics.append(self._diagnostic(
                "emerge-missing",
                DiagnosticLevel.ERROR,
                "Portage emerge is not installed",
                detail="Cannot perform Gentoo diagnostics because `emerge` is unavailable.",
            ))
            status = "FAILED"
        else:
            diagnostics.append(self._check_world_update_plan())
            profile_warning = self._check_profile(system_context)
            if profile_warning:
                diagnostics.append(profile_warning)
            status = "SUCCESS"

        return self._build_report(
            command="check",
            status=status,
            system_context=system_context,
            diagnostics=diagnostics,
            actions=[{"note": "Aegis Maintenance Gentoo check completed."}],
            metadata={"backend_family": self.family},
        )

    def update(self, system_context: Any):
        return self._build_report(
            command="update",
            status="ACTION_REQUIRED",
            system_context=system_context,
            diagnostics=[self._diagnostic("update-not-implemented", DiagnosticLevel.UNKNOWN, "Gentoo update not implemented")],
        )

    def clean(self, system_context: Any):
        return self._build_report(
            command="clean",
            status="SUCCESS_WITH_NOTICES",
            system_context=system_context,
            diagnostics=[self._diagnostic("clean-not-implemented", DiagnosticLevel.UNKNOWN, "Gentoo clean not implemented")],
        )

    def report(self, system_context: Any):
        return self._build_report(
            command="report",
            status="SUCCESS",
            system_context=system_context,
            diagnostics=[self._diagnostic("report-skeleton", DiagnosticLevel.INFO, "Gentoo report skeleton")],
        )

    def doctor(self, system_context: Any):
        return self._build_report(
            command="doctor",
            status="UNKNOWN",
            system_context=system_context,
            diagnostics=[self._diagnostic("doctor-skeleton", DiagnosticLevel.UNKNOWN, "Gentoo doctor skeleton")],
        )

    def _check_world_update_plan(self):
        result = self.executor.run([
            "emerge",
            "--pretend",
            "--update",
            "--deep",
            "--with-bdeps=y",
            "@world",
        ])
        if result.returncode != 0:
            return self._diagnostic(
                "gentoo-update-plan-failed",
                DiagnosticLevel.WARNING,
                "Unable to calculate Gentoo world update plan",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        level = DiagnosticLevel.NOTICE if result.stdout else DiagnosticLevel.OK
        title = "Gentoo world update candidates found" if result.stdout else "Gentoo world is up to date"
        return self._diagnostic(
            "gentoo-world-plan",
            level,
            title,
            detail=result.stdout,
            data={"command": result.command},
        )

    def _check_profile(self, system_context: Any) -> Optional[Dict[str, Any]]:
        profile = system_context.os_release.get("VARIANT_ID") or system_context.os_release.get("ID")
        if profile and profile != "gentoo":
            return self._diagnostic(
                "profile-variant",
                DiagnosticLevel.INFO,
                "Gentoo profile variant detected",
                detail=f"Detected {profile}",
            )
        return None
