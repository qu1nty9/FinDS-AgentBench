from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from finds_agentbench.runs import utc_now


@dataclass(frozen=True)
class AgentCommandResult:
    command: list[str]
    started_at: str
    completed_at: str
    exit_code: int
    timed_out: bool
    stdout_path: Path
    stderr_path: Path

    @property
    def command_string(self) -> str:
        return " ".join(shlex.quote(part) for part in self.command)

    def as_manifest_command(self) -> dict[str, object]:
        return {
            "command": self.command_string,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "stdout_path": str(self.stdout_path),
            "stderr_path": str(self.stderr_path),
        }


def normalize_command(command: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(command, str):
        parsed = shlex.split(command)
    else:
        parsed = [str(part) for part in command]
    if not parsed:
        raise ValueError("agent command must be non-empty")
    return parsed


def run_agent_command(
    *,
    command: str | list[str] | tuple[str, ...],
    env: dict[str, str],
    cwd: str | Path | None,
    log_dir: str | Path,
    timeout_seconds: int,
) -> AgentCommandResult:
    command_parts = normalize_command(command)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    stdout_path = log_path / "stdout.txt"
    stderr_path = log_path / "stderr.txt"
    merged_env = os.environ.copy()
    merged_env.update(env)

    started_at = utc_now()
    try:
        completed = subprocess.run(
            command_parts,
            cwd=Path(cwd) if cwd is not None else None,
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        completed_at = utc_now()
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        exit_code = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        completed_at = utc_now()
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode(
            errors="replace"
        )
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode(
            errors="replace"
        )
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr + "\nagent_command_timed_out\n", encoding="utf-8")
        exit_code = 124
        timed_out = True

    return AgentCommandResult(
        command=command_parts,
        started_at=started_at,
        completed_at=completed_at,
        exit_code=exit_code,
        timed_out=timed_out,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
