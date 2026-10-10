"""Cloud-free structural checks; intentionally not a Snowflake syntax proof."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "00_cost_guardrails.sql",
    "01_governed_database_and_roles.sql",
    "02_session_observability.sql",
}
UNSAFE = (
    r"\bDROP\s+(?:DATABASE|SCHEMA|WAREHOUSE|ROLE)\b",
    r"\bCREATE\s+OR\s+REPLACE\b",
    r"\bAUTO_RESUME\s*=\s*TRUE\b",
    r"\bPASSWORD\s*=",
    r"\b(?:USE\s+WAREHOUSE|ALTER\s+WAREHOUSE\s+\w+\s+RESUME)\b",
)


def validate_reference(root: Path = ROOT) -> list[str]:
    folder = root / "snowflake" / "sql"
    files = {file.name for file in folder.glob("*.sql")}
    errors = []
    if files != EXPECTED:
        errors.append("Snowflake reference file inventory differs from allowlist")
    for name in EXPECTED & files:
        content = (folder / name).read_text(encoding="utf-8")
        if not content.startswith("-- STATIC REFERENCE ONLY."):
            errors.append(f"missing non-execution header: {name}")
        if not content.rstrip().endswith(";"):
            errors.append(f"missing terminating semicolon: {name}")
        for pattern in UNSAFE:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(f"unsafe SQL pattern {pattern!r}: {name}")
    guardrails = folder / "00_cost_guardrails.sql"
    if guardrails.is_file():
        text = guardrails.read_text(encoding="utf-8").upper()
        for marker in (
            "CREDIT_QUOTA = 10",
            "SUSPEND_IMMEDIATE",
            "WAREHOUSE_SIZE = XSMALL",
            "AUTO_SUSPEND = 60",
            "AUTO_RESUME = FALSE",
            "INITIALLY_SUSPENDED = TRUE",
            "RESOURCE_MONITOR = SAAS_EXAMPLE_MONITOR",
        ):
            if marker not in text:
                errors.append(f"missing cost guardrail: {marker}")
    grants = folder / "01_governed_database_and_roles.sql"
    if grants.is_file():
        text = grants.read_text(encoding="utf-8").upper()
        if "GRANT SELECT ON FUTURE VIEWS IN SCHEMA SAAS_EXAMPLE_DB.MARTS" not in text:
            errors.append("future certified-view grant missing")
        raw_reader_grant = (
            r"(?m)^GRANT\s+[^;\n]*SAAS_EXAMPLE_DB\.RAW"
            r"\s+TO\s+ROLE\s+SAAS_EXAMPLE_FABRIC_READER_ROLE\s*;"
        )
        if re.search(raw_reader_grant, text):
            errors.append("Fabric reader must not receive RAW access")
    return errors


if __name__ == "__main__":
    failures = validate_reference()
    if failures:
        raise SystemExit("\n".join(failures))
    print("Snowflake static reference checks passed; no SQL executed")
