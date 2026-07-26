from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class DiagnosticLevel(Enum):
    OK = "OK"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class Diagnostic:
    id: str
    level: DiagnosticLevel
    title: str
    detail: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level.value,
            "title": self.title,
            "detail": self.detail,
            "data": self.data,
        }
