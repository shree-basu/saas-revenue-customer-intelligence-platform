"""Reject accidental cloud execution paths and credential-shaped tracked files."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE_SUFFIXES = {".py", ".sh", ".ps1", ".bat", ".cmd", ".yml", ".yaml"}
BANNED_EXECUTION = [
    r"id-token\s*:\s*write",
    r"secrets\s*\.",
    r"workflow_dispatch",
    r"pull_request_target",
    r"self-hosted",
    r"google-github-actions/auth",
    r"azure/login",
    r"\baz\s+login\b",
    r"Connect-AzAccount",
    r"\bsnow\s+sql\b",
    r"\bsnowsql\b",
    r"snowflake\.connector\.connect",
    r"\bterraform\s+(?:apply|destroy)\b",
    r"\bdocker\s+push\b",
    r"api\.fabric\.microsoft\.com",
    r"\bdbt\s+(?:run|build|test)\s+--target\s+snowflake\b",
]
CREDENTIAL_PATTERNS = [
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"(?i)(?:client_secret|access_token|refresh_token|snowflake_password)\s*[:=]\s*['\"]?[A-Za-z0-9_+/=-]{12,}",
]


def tracked_files() -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    return [ROOT / Path(item.decode()) for item in result.stdout.split(b"\0") if item]


def check() -> list[str]:
    errors: list[str] = []
    for path in tracked_files():
        relative = path.relative_to(ROOT).as_posix()
        if not path.is_file():
            continue
        if path.name == ".env" or path.name.startswith(".env.") and path.name != ".env.example":
            errors.append(f"tracked environment file: {relative}")
        if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            errors.append(f"tracked key-like file: {relative}")
        if path.suffix.lower() not in EXECUTABLE_SUFFIXES and path.suffix.lower() not in {
            ".json",
            ".toml",
            ".sql",
            ".tmdl",
        }:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        for pattern in CREDENTIAL_PATTERNS:
            if re.search(pattern, content):
                errors.append(f"credential pattern in {relative}")
        executable = (
            relative.startswith(".github/workflows/") or relative.startswith("scripts/")
        ) and path.name != Path(__file__).name
        if executable:
            for pattern in BANNED_EXECUTION:
                if re.search(pattern, content, flags=re.IGNORECASE):
                    errors.append(f"unsafe executable pattern {pattern!r} in {relative}")
        if relative.startswith(".github/workflows/"):
            if not re.search(r"(?m)^\s*permissions:\s*\n\s*contents:\s*read\s*$", content):
                errors.append(f"workflow lacks read-only permissions: {relative}")
            for runner in re.findall(r"(?m)^\s*runs-on:\s*([^\r\n]+)", content):
                if runner.strip() != "ubuntu-latest":
                    errors.append(f"nonstandard runner: {relative}")
            for action in re.findall(r"(?m)^\s*-?\s*uses:\s*([^\s#]+)", content):
                if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}", action):
                    errors.append(f"un-pinned action {action}: {relative}")
    return errors


if __name__ == "__main__":
    failures = check()
    if failures:
        raise SystemExit("\n".join(failures))
    print("Repository safety checks passed")
