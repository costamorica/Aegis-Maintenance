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
        diagnostics.append(self._check_orphans())
        diagnostics.append(self._check_foreign_packages())
        diagnostics.append(self._check_pacman_cache())
        diagnostics.append(self._check_systemd_failed_services())
        diagnostics.append(self._check_root_filesystem())
        diagnostics.append(self._check_disk_space())
        diagnostics.append(self._check_reboot_recommended())
        diagnostics.append(self._check_pacsave())
        diagnostics.append(self._check_pacnew())

        return self._build_report(
            command="check",
            status=self._status_from_diagnostics(diagnostics),
            system_context=system_context,
            diagnostics=diagnostics,
            actions=[{"note": "Aegis Maintenance EndeavourOS check completed."}],
            metadata={"backend_family": self.family},
        )

    def update(self, system_context: Any):
        diagnostics: List[Dict[str, Any]] = []

        status, result = self._check_updates_available()
        if status == "available":
            diagnostics.append(self._diagnostic(
                "update-plan-available",
                DiagnosticLevel.NOTICE,
                "EndeavourOS package updates are available",
                detail=result.stdout,
                data={"command": result.command},
            ))
        elif status == "none":
            diagnostics.append(self._diagnostic(
                "update-plan-none",
                DiagnosticLevel.OK,
                "No package updates are currently available",
                detail=result.stdout,
                data={"command": result.command},
            ))
        else:
            diagnostics.append(self._diagnostic(
                "update-plan-failed",
                DiagnosticLevel.WARNING,
                "Unable to determine package update plan",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            ))

        diagnostics.append(self._diagnostic(
            "update-plan-summary",
            DiagnosticLevel.INFO,
            "Mode: update plan",
            detail="Changes performed: none. This command only generates a read-only plan.",
            data={"command": result.command},
        ))

        return self._build_report(
            command="update",
            status=self._status_from_diagnostics(diagnostics),
            system_context=system_context,
            diagnostics=diagnostics,
            actions=[{"note": "Mode: update plan; Changes performed: none."}],
            metadata={
                "backend_family": self.family,
                "plan_mode": "update",
                "changes_performed": "none",
                "dry_run": True,
            },
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

    def _check_updates_available(self):
        updater = "checkupdates" if self.executor.which("checkupdates") else None
        if updater:
            result = self.executor.run([updater])
            if result.returncode == 0:
                return "none", result
            if result.returncode == 2 and result.stdout:
                return "available", result
            return "failed", result

        result = self.executor.run(["pacman", "-Qu"])
        if result.returncode == 0:
            if result.stdout:
                return "available", result
            return "none", result
        return "failed", result

    def _check_pacman_update(self):
        status, result = self._check_updates_available()
        if status == "available":
            return self._diagnostic(
                "updates-available",
                DiagnosticLevel.NOTICE,
                "Pacman updates are available",
                detail=result.stdout,
                data={"command": result.command},
            )
        if status == "failed":
            return self._diagnostic(
                "updates-check-failed",
                DiagnosticLevel.WARNING,
                "Unable to check Pacman updates",
                detail=result.stderr or result.stdout,
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

    def _check_orphans(self):
        result = self.executor.run(["pacman", "-Qdtq"])
        if result.returncode == 0 and result.stdout:
            return self._diagnostic(
                "orphans-found",
                DiagnosticLevel.NOTICE,
                "Orphan packages detected",
                detail=result.stdout,
                data={"command": result.command},
            )
        if result.returncode in {0, 1} and not result.stdout:
            return self._diagnostic(
                "orphans-none",
                DiagnosticLevel.OK,
                "No orphan packages found",
                detail="",
                data={"command": result.command},
            )
        return self._diagnostic(
            "orphans-check-failed",
            DiagnosticLevel.WARNING,
            "Unable to determine orphan packages",
            detail=result.stderr or result.stdout,
            data={"command": result.command},
        )

    def _check_foreign_packages(self):
        result = self.executor.run(["pacman", "-Qm"])
        if result.returncode == 0 and result.stdout:
            return self._diagnostic(
                "foreign-packages-found",
                DiagnosticLevel.NOTICE,
                "Foreign packages detected",
                detail=result.stdout,
                data={"command": result.command},
            )
        if result.returncode in {0, 1} and not result.stdout:
            return self._diagnostic(
                "foreign-packages-none",
                DiagnosticLevel.OK,
                "No foreign packages found",
                detail="",
                data={"command": result.command},
            )
        return self._diagnostic(
            "foreign-packages-failed",
            DiagnosticLevel.WARNING,
            "Unable to determine foreign packages",
            detail=result.stderr or result.stdout,
            data={"command": result.command},
        )

    def _check_pacman_cache(self):
        result = self.executor.run(["bash", "-lc", "du -sh /var/cache/pacman/pkg 2>/dev/null || true"])
        if result.returncode != 0:
            return self._diagnostic(
                "pacman-cache-failed",
                DiagnosticLevel.WARNING,
                "Unable to determine pacman cache size",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        return self._diagnostic(
            "pacman-cache-size",
            DiagnosticLevel.INFO,
            "Pacman package cache size",
            detail=result.stdout.strip(),
            data={"command": result.command},
        )

    def _check_systemd_failed_services(self):
        result = self.executor.run(["systemctl", "list-units", "--state=failed", "--no-pager", "--no-legend"])
        if result.returncode != 0:
            return self._diagnostic(
                "systemd-failed-services-failed",
                DiagnosticLevel.WARNING,
                "Unable to determine failed systemd services",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        if result.stdout:
            return self._diagnostic(
                "systemd-failed-services",
                DiagnosticLevel.WARNING,
                "Failed systemd services detected",
                detail=result.stdout,
                data={"command": result.command},
            )
        return self._diagnostic(
            "systemd-failed-services-none",
            DiagnosticLevel.OK,
            "No failed systemd services found",
            detail="",
            data={"command": result.command},
        )

    def _check_root_filesystem(self):
        result = self.executor.run(["bash", "-lc", "findmnt -n -o SOURCE,TARGET / | tr -s ' '"],)
        if result.returncode != 0:
            return self._diagnostic(
                "root-filesystem-failed",
                DiagnosticLevel.WARNING,
                "Unable to determine root filesystem",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        return self._diagnostic(
            "root-filesystem",
            DiagnosticLevel.INFO,
            "Root filesystem information",
            detail=result.stdout,
            data={"command": result.command},
        )

    def _check_disk_space(self):
        result = self.executor.run(["df", "-h", "/"])
        if result.returncode != 0:
            return self._diagnostic(
                "disk-space-failed",
                DiagnosticLevel.WARNING,
                "Unable to determine root filesystem space",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        return self._diagnostic(
            "disk-space",
            DiagnosticLevel.INFO,
            "Root filesystem disk space",
            detail=result.stdout,
            data={"command": result.command},
        )

    def _check_reboot_recommended(self):
        result = self.executor.run(["bash", "-lc", "[ -f /var/run/reboot-required ] && echo reboot-required || true"])
        if result.returncode != 0:
            return self._diagnostic(
                "reboot-check-failed",
                DiagnosticLevel.WARNING,
                "Unable to determine reboot recommendation",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        if result.stdout.strip() == "reboot-required":
            return self._diagnostic(
                "reboot-required",
                DiagnosticLevel.WARNING,
                "Reboot is recommended",
                detail="/var/run/reboot-required was detected.",
                data={"command": result.command},
            )
        return self._diagnostic(
            "reboot-not-required",
            DiagnosticLevel.OK,
            "No reboot is currently recommended",
            detail="",
            data={"command": result.command},
        )

    def _check_pacsave(self):
        result = self.executor.run(["bash", "-lc", "find /etc -name '*.pacsave' 2>/dev/null | head -n 20"])
        if result.returncode != 0:
            return self._diagnostic(
                "pacsave-check-failed",
                DiagnosticLevel.WARNING,
                "Unable to search for .pacsave files",
                detail=result.stderr or result.stdout,
                data={"command": result.command},
            )
        if result.stdout:
            return self._diagnostic(
                "pacsave-files",
                DiagnosticLevel.NOTICE,
                ".pacsave files found",
                detail=result.stdout,
                data={"command": result.command},
            )
        return self._diagnostic(
            "pacsave-none",
            DiagnosticLevel.OK,
            "No .pacsave files found",
            detail="",
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
