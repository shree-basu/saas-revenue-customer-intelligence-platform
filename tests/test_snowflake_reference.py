"""Cloud-free checks for static Snowflake design controls."""

from __future__ import annotations

import shutil
from pathlib import Path

from scripts.validate_snowflake_reference import ROOT, validate_reference


def test_static_reference_passes() -> None:
    assert validate_reference() == []


def test_missing_guardrail_fails(tmp_path: Path) -> None:
    target = tmp_path / "snowflake" / "sql"
    shutil.copytree(ROOT / "snowflake" / "sql", target)
    script = target / "00_cost_guardrails.sql"
    script.write_text(
        script.read_text(encoding="utf-8").replace("AUTO_RESUME = FALSE", "AUTO_RESUME = TRUE"),
        encoding="utf-8",
    )
    assert any("AUTO_RESUME" in message for message in validate_reference(tmp_path))


def test_fabric_reader_cannot_gain_raw_grant(tmp_path: Path) -> None:
    target = tmp_path / "snowflake" / "sql"
    shutil.copytree(ROOT / "snowflake" / "sql", target)
    script = target / "01_governed_database_and_roles.sql"
    script.write_text(
        script.read_text(encoding="utf-8")
        + "\nGRANT SELECT ON ALL TABLES IN SCHEMA SAAS_EXAMPLE_DB.RAW "
        "TO ROLE SAAS_EXAMPLE_FABRIC_READER_ROLE;\n",
        encoding="utf-8",
    )
    assert any("RAW access" in message for message in validate_reference(tmp_path))


def test_diagnostic_worksheet_cannot_mutate(tmp_path: Path) -> None:
    target = tmp_path / "snowflake" / "sql"
    shutil.copytree(ROOT / "snowflake" / "sql", target)
    script = target / "03_diagnostic_queries.sql"
    script.write_text(
        script.read_text(encoding="utf-8") + "\nALTER TABLE X CLUSTER BY (D);\n", encoding="utf-8"
    )
    assert any("read-only" in message for message in validate_reference(tmp_path))
