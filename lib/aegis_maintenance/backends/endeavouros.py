from typing import Any, Dict, List

from aegis_maintenance.backends.base import Backend
from aegis_maintenance.diagnostics import DiagnosticLevel


class EndeavourOSBackend(Backend):
    identifier = "endeavouros"
    priority = 10
    supported_distributions = ("endeavouros",)
    family = "arch"

    def matches(self, system_context: Any) -> bool:
        distribution = (getattr(system_context, "distribution_id", None) or "").lower()
        os_release = getattr(system_context, "os_release", {}) or {}
        id_like = os_release.get("ID_LIKE", "").lower()
        return distribution == "endeavouros" or "endeavouros" in id_like

    def check(self, system_context: Any):
        diagnostics: List[Dict[str, Any]] = []

        diagnostics.append(self._check_eos_tools())
        diagnostics.append(self._check_endeavouros_repo())
        diagnostics.append(self._check_pacman_update())
        diagnostics.append(self._check_pacman_db())
        diagnostics.append(self._check_pacnew())

        return self._build_report(
            command="check",
            status="SUCCESS",
            system_context=system_context,
            diagnostics=diagnostics,
            actions=[{"note": "Aegis Maintenance EndeavourOS check completed."}],
            metadata={"backend_family": self.family},
        )

    def update(self, system_context: Any):
        return self._build_report(
            command="update",
            status="ACTION_REQUIRED",
            system_context=system_context,
            diagnostics=[self._diagnostic("update-not-implemented", DiagnosticLevel.UNKNOWN, "EndeavourOS update not implemented")],
        )

    def clean(self, system_context: Any):
        return self._build_report(
            command="clean",
            status="SUCCESS_WITH_NOTICES",
            system_context=system_context,
            diagnostics=[self._diagnostic("clean-not-implemented", DiagnosticLevel.UNKNOWN, "EndeavourOS clean not implemented")],
        )

    def report(self, system_context: Any):
        return self._build_report(
            command="report",
            status="SUCCESS",
            system_context=system_context,
            diagnostics=[self._diagnostic("report-skeleton", DiagnosticLevel.INFO, "EndeavourOS report skeleton")],
        )

    def doctor(self, system_context: Any):
        return self._build_report(
            command="doctor",
            status="UNKNOWN",
            system_context=system_context,
            diagnostics=[self._diagnostic("doctor-skeleton", DiagnosticLevel.UNKNOWN, "EndeavourOS doctor skeleton")],
        )

    def _check_eos_tools(self):
        if self.executor.which("eos-rankmirrors"):
            return self._diagnostic(
                "eos-tools-present",
                DiagnosticLevel.OK,
                "EndeavourOS tools are available",
                detail="eos-rankmirrors is present on PATH.",
            )
        return self._diagnostic(
            "eos-tools-missing",
            DiagnosticLevel.INFO,
            "EndeavourOS helper tools are not installed",
            detail="eos-rankmirrors was not found on PATH.",
        )

    def _check_endeavouros_repo(self):
        result = self.executor.run(["bash", "-lc", "grep -E '^\\[endeavouros\\]' /etc/pacman.conf 2>/dev/null | head -n 1"])
        if result.returncode != 0:
            return self._diagnostic(
                "eos-repo-check-failed",
                DiagnosticLevel.WARNING,
                "Unable to verify EndeavourOS repository configuration",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        if result.stdout:
            return self._diagnostic(
                "eos-repo-present",
                DiagnosticLevel.OK,
                "EndeavourOS repository configuration detected",
                detail=result.stdout,
                data={"command": result.command},
            )
        return self._diagnostic(
            "eos-repo-missing",
            DiagnosticLevel.INFO,
            "EndeavourOS repository configuration is not detected",
            detail="No [endeavouros] repository section found in /etc/pacman.conf.",
            data={"command": result.command},
        )

    def _check_pacman_update(self):
        updater = "checkupdates" if self.executor.which("checkupdates") else None
        if updater:
            result = self.executor.run([updater])
        else:
            result = self.executor.run(["pacman", "-Qu"])

        if result.returncode == 0 and result.stdout:
            return self._diagnostic(
                "updates-available",
                DiagnosticLevel.NOTICE,
                "Pacman updates are available",
                detail=result.stdout,
                data={"command": result.command},
            )
        if result.returncode != 0 and result.stderr:
            return self._diagnostic(
                "updates-check-failed",
                DiagnosticLevel.WARNING,
                "Unable to check Pacman updates",
                detail=result.stderr,
                data={"command": result.command},
            )
        return self._diagnostic(
            "updates-none",
            DiagnosticLevel.OK,
            "No Pacman updates found",
            detail=result.stdout,
            data={"command": result.command},
        )

    def _check_pacman_db(self):
        result = self.executor.run(["pacman", "-Dk"])
        if result.returncode != 0:
            return self._diagnostic(
                "pacman-db-error",
                DiagnosticLevel.WARNING,
                "Pacman database check failed",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        return self._diagnostic(
            "pacman-db-ok",
            DiagnosticLevel.OK,
            "Pacman database is consistent",
            detail=result.stdout,
            data={"command": result.command},
        )

    def _check_pacnew(self):
        result = self.executor.run(["bash", "-lc", "find /etc -name '*.pacnew' 2>/dev/null | head -n 20"])
        if result.returncode != 0:
            return self._diagnostic(
                "pacnew-check-failed",
                DiagnosticLevel.WARNING,
                "Failed to search for .pacnew files",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        if result.stdout:
            return self._diagnostic(
                "pacnew-files",
                DiagnosticLevel.NOTICE,
                ".pacnew files found",
                detail=result.stdout,
                data={"command": result.command},
            )
        return self._diagnostic(
            "pacnew-none",
            DiagnosticLevel.OK,
            "No .pacnew files found",
            detail="",
            data={"command": result.command},
        )
