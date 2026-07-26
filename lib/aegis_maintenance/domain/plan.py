from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionAction:
    id: str
    description: str
    details: Optional[str] = None
    needs_sudo: bool = False
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "details": self.details,
            "needs_sudo": self.needs_sudo,
            "metadata": self.metadata or {},
        }


@dataclass
class ExecutionPlan:
    backend: str
    command: str
    distribution: str
    summary: str
    package_changes: List[str]
    actions: List[ExecutionAction]
    diagnostics: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    needs_confirmation: bool = True
    needs_sudo: bool = True
    can_rollback: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "command": self.command,
            "distribution": self.distribution,
            "summary": self.summary,
            "package_changes": self.package_changes,
            "actions": [action.to_dict() for action in self.actions],
            "diagnostics": self.diagnostics,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "needs_confirmation": self.needs_confirmation,
            "needs_sudo": self.needs_sudo,
            "can_rollback": self.can_rollback,
        }
