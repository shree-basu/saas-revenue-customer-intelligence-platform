"""Cloud-free dbt merge proof for new, corrected, late and replayed records."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from data.contracts import ContractViolation
from data.generate_saas_batch import generate_batch
from local.landing import load_delivery

ROOT = Path(__file__).resolve().parents[1]


def _build(database: Path, selector: str | None = None) -> None:
    executable = Path(sys.executable).with_name("dbt.exe" if os.name == "nt" else "dbt")
    command = [
        str(executable),
        "build",
        "--project-dir",
        str(ROOT / "dbt"),
        "--profiles-dir",
        str(ROOT / "dbt"),
        "--target",
        "local",
        "--quiet",
    ]
    if selector:
        command.extend(["--select", selector])
    result = subprocess.run(
        command,
        cwd=ROOT,
        env={**os.environ, "SAAS_DUCKDB_PATH": str(database)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]


def _facts(database: Path) -> tuple:
    with duckdb.connect(str(database), read_only=True) as connection:
        invoice = connection.execute(
            "select invoice_date, amount from fct_invoices where invoice_id = 'I00001'"
        ).fetchone()
        usage = connection.execute(
            "select usage_minutes from fct_product_usage_daily where account_id = 'A00001'"
        ).fetchone()
        counts = tuple(
            connection.execute(f"select count(*) from {table}").fetchone()[0]
            for table in ("fct_invoices", "fct_product_usage_daily", "fct_support_cases")
        )
        duplicate_keys = connection.execute(
            "select count(*) - count(distinct invoice_id) from fct_invoices"
        ).fetchone()[0]
    return invoice, usage, counts, duplicate_keys


def test_incremental_merge_handles_new_late_updated_and_retry(tmp_path: Path) -> None:
    database = tmp_path / "replay.duckdb"
    first = generate_batch(tmp_path / "deliveries", "2026-10-09", "initial", 17, 12, "normal")
    load_delivery(first, database)
    _build(database)
    initial = _facts(database)
    assert initial[0] == (date(2026, 10, 9), Decimal("103.00"))
    assert initial[1] == (107,)
    assert initial[2:] == ((12, 12, 12), 0)

    correction = generate_batch(
        tmp_path / "deliveries", "2026-10-09", "corrected", 17, 13, "late-correction"
    )
    load_delivery(correction, database)
    _build(database)
    updated = _facts(database)
    assert updated[0] == (date(2026, 10, 9) - timedelta(days=35), Decimal("110.00"))
    assert updated[1] == (118,)
    assert updated[2:] == ((13, 13, 13), 0)

    _build(database)  # identical source retry must not add a second row or undo the correction
    assert _facts(database) == updated

    account_change = generate_batch(
        tmp_path / "deliveries", "2026-10-09", "account-revised", 17, 13, "account-correction"
    )
    load_delivery(account_change, database)
    _build(database, "+snap_account_history")
    with duckdb.connect(str(database), read_only=True) as connection:
        versions = connection.execute(
            "select account_name, dbt_valid_from, dbt_valid_to "
            "from main_snapshots.snap_account_history "
            "where account_id = 'A00001' order by dbt_valid_from"
        ).fetchall()
    assert len(versions) == 2
    assert versions[0][0] == "Synthetic Customer 1"
    assert versions[1][0] == "Synthetic Customer 1 Revised"
    assert versions[0][2] == versions[1][1]
    assert versions[1][2] is None

    _build(database, "+snap_account_history")  # snapshot retry is idempotent
    with duckdb.connect(str(database), read_only=True) as connection:
        assert (
            connection.execute(
                "select count(*) from main_snapshots.snap_account_history "
                "where account_id = 'A00001'"
            ).fetchone()[0]
            == 2
        )

    with pytest.raises(ContractViolation, match="out-of-order"):
        load_delivery(correction, database)  # older account state cannot overwrite newer state
    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute(
            "select account_name from raw.accounts where account_id = 'A00001'"
        ).fetchone() == ("Synthetic Customer 1 Revised",)
