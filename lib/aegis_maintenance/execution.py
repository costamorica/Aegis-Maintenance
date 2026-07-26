import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CommandResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


class CommandExecutor:
    def __init__(self, env: Optional[Dict[str, str]] = None, timeout: int = 30):
        self.env = env if env is not None else os.environ.copy()
        self.timeout = timeout

    def run(self, args: List[str], cwd: Optional[str] = None) -> CommandResult:
        try:
            proc = subprocess.run(
                args,
                cwd=cwd,
                env=self.env,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return CommandResult(
                command=args,
                returncode=proc.returncode,
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            return CommandResult(
                command=args,
                returncode=-1,
                stdout=stdout.strip(),
                stderr=stderr.strip() or "command timed out",
                timed_out=True,
            )

    @staticmethod
    def which(executable: str) -> Optional[str]:
        from shutil import which

        return which(executable)
