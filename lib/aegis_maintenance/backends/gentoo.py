import os
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
        else:
            diagnostics.append(self._check_world_update_plan())
            profile_warning = self._check_profile(system_context)
            if profile_warning:
                diagnostics.append(profile_warning)

        status = self._status_from_diagnostics(diagnostics)
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
            "--newuse",
            "--with-bdeps=y",
            "@world",
        ])
        if result.returncode != 0:
            return self._diagnostic(
                "gentoo-update-plan-failed",
                DiagnosticLevel.ERROR,
                "Unable to calculate Gentoo world update plan",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )

        candidates = self._parse_emerge_world_plan(result.stdout)
        if candidates:
            return self._diagnostic(
                "gentoo-world-plan",
                DiagnosticLevel.NOTICE,
                "Gentoo world update candidates found",
                detail="\n".join(candidates),
                data={"command": result.command},
            )

        return self._diagnostic(
            "gentoo-world-plan",
            DiagnosticLevel.OK,
            "Gentoo world is up to date",
            detail="No packages were selected for update by emerge.",
            data={"command": result.command},
        )

    def _parse_emerge_world_plan(self, output: str) -> List[str]:
        if not output:
            return []

        lower = output.lower()
        if "no packages to merge" in lower or "nothing to merge" in lower:
            return []

        candidates: List[str] = []
        for line in output.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(">>>"):
                continue
            if stripped.startswith("*") or stripped.startswith("[ebuild]"):
                candidates.append(stripped)
                continue
            if "ebuild" in stripped and "from" in stripped:
                candidates.append(stripped)
                continue
            if stripped.startswith("+ ") or stripped.startswith("- "):
                candidates.append(stripped)
                continue
        return candidates

    def _check_profile(self, system_context: Any) -> Optional[Dict[str, Any]]:
        profile = self._detect_portage_profile()
        if profile and profile != "gentoo":
            return self._diagnostic(
                "profile-path",
                DiagnosticLevel.INFO,
                "Gentoo Portage profile detected",
                detail=profile,
            )
        return None

    def _detect_portage_profile(self) -> Optional[str]:
        profile_path = "/etc/portage/make.profile"
        if os.path.exists(profile_path):
            try:
                if os.path.islink(profile_path):
                    profile = os.readlink(profile_path)
                else:
                    with open(profile_path, "r", encoding="utf-8") as fh:
                        profile = fh.read().strip()
                if profile:
                    if not os.path.isabs(profile):
                        profile = os.path.normpath(os.path.join(os.path.dirname(profile_path), profile))
                    return profile
            except OSError:
                return None
        return None
