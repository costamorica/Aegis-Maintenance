from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Report:
    id: str
    timestamp: datetime
    backend: str
    distribution: str
    command: str
    status: str
    diagnostics: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "backend": self.backend,
            "distribution": self.distribution,
            "command": self.command,
            "status": self.status,
            "diagnostics": self.diagnostics,
            "actions": self.actions,
            "metadata": self.metadata or {},
        }
