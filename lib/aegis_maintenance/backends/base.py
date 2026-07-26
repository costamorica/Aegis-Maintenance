from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from aegis_maintenance.diagnostics import Diagnostic, DiagnosticLevel
from aegis_maintenance.domain.report import Report
from aegis_maintenance.execution import CommandExecutor


class Backend(ABC):
    def __init__(self):
        self.executor = CommandExecutor()

    @property
    @abstractmethod
    def identifier(self) -> str:
        raise NotImplementedError

    @property
    def priority(self) -> int:
        return 0

    def matches(self, system_context: Any) -> bool:
        return False

    @abstractmethod
    def check(self, system_context: Any) -> Report:
        raise NotImplementedError

    @abstractmethod
    def update(self, system_context: Any) -> Report:
        raise NotImplementedError

    @abstractmethod
    def clean(self, system_context: Any) -> Report:
        raise NotImplementedError

    @abstractmethod
    def report(self, system_context: Any) -> Report:
        raise NotImplementedError

    @abstractmethod
    def doctor(self, system_context: Any) -> Report:
        raise NotImplementedError

    def _build_report(
        self,
        command: str,
        status: str,
        system_context: Any,
        diagnostics: List[Dict[str, Any]],
        actions: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Report:
        return Report(
            id=f"{self.identifier}-{command}-{self._timestamp()}" ,
            timestamp=self._now(),
            backend=self.identifier,
            distribution=system_context.distribution_id or "unknown",
            command=command,
            status=status,
            diagnostics=diagnostics,
            actions=actions or [],
            metadata=metadata or {},
        )

    def _diagnostic(
        self,
        id: str,
        level: DiagnosticLevel,
        title: str,
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return Diagnostic(id=id, level=level, title=title, detail=detail, data=data).to_dict()

    def _now(self):
        from datetime import datetime

        return datetime.utcnow()

    def _timestamp(self) -> str:
        return self._now().strftime("%Y%m%d%H%M%S")

    def _status_from_diagnostics(self, diagnostics: List[Dict[str, Any]]) -> str:
        levels = {diag.get("level") for diag in diagnostics}
        if "CRITICAL" in levels or "ERROR" in levels:
            return "FAILED"
        if "WARNING" in levels or "NOTICE" in levels:
            return "SUCCESS_WITH_NOTICES"
        if "OK" in levels or "INFO" in levels:
            return "SUCCESS"
        return "UNKNOWN"
