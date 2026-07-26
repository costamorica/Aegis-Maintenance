from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionAction:
    id: str
    description: str
    details: Optional[str] = None
    needs_sudo: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "details": self.details,
            "needs_sudo": self.needs_sudo,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionPlan:
    backend: str
    command: str
    distribution: str
    summary: str
    package_changes: List[str] = field(default_factory=list)
    actions: List[ExecutionAction] = field(default_factory=list)
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    dry_run: bool = True
    needs_confirmation: bool = True
    needs_sudo: bool = False
    can_rollback: bool = False
    rollback_policy: Optional[str] = None

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
            "preconditions": self.preconditions,
            "dry_run": self.dry_run,
            "needs_confirmation": self.needs_confirmation,
            "needs_sudo": self.needs_sudo,
            "can_rollback": self.can_rollback,
            "rollback_policy": self.rollback_policy,
        }
