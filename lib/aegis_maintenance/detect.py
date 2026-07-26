import os
import platform
import shlex
import socket
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SystemContext:
    distribution_id: Optional[str]
    distribution_name: Optional[str]
    version_id: Optional[str]
    pretty_name: Optional[str]
    id_like: List[str]
    architecture: Optional[str]
    kernel: Optional[str]
    hostname: Optional[str]
    init_system: Optional[str]
    os_release: Dict[str, str]


class SystemDetector:
    OS_RELEASE_PATH = "/etc/os-release"

    def detect(self) -> SystemContext:
        os_release = self._load_os_release()
        id_like = self._parse_id_like(os_release.get("ID_LIKE", ""))
        return SystemContext(
            distribution_id=os_release.get("ID"),
            distribution_name=os_release.get("NAME"),
            version_id=os_release.get("VERSION_ID"),
            pretty_name=os_release.get("PRETTY_NAME"),
            id_like=id_like,
            architecture=platform.machine(),
            kernel=platform.release(),
            hostname=socket.gethostname(),
            init_system=self._detect_init_system(),
            os_release=os_release,
        )

    def _parse_id_like(self, id_like_value: str) -> List[str]:
        return [item.strip().lower() for item in shlex.split(id_like_value) if item.strip()]

    def _detect_init_system(self) -> Optional[str]:
        proc_comm = "/proc/1/comm"
        if os.path.exists(proc_comm):
            try:
                with open(proc_comm, "r", encoding="utf-8") as fh:
                    return fh.read().strip()
            except OSError:
                return None
        return None

    def _load_os_release(self) -> Dict[str, str]:
        data = {}
        if not os.path.exists(self.OS_RELEASE_PATH):
            return data
        with open(self.OS_RELEASE_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                data[key] = value
        return data
