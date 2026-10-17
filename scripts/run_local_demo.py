"""Reproducible zero-cloud SaaS replay demonstration in a temporary directory."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from data.generate_saas_batch import generate_batch
from local.landing import load_delivery

ROOT = Path(__file__).resolve().parents[1]


def _build(database: Path) -> None:
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
    result = subprocess.run(
        command,
        cwd=ROOT,
        env={**os.environ, "SAAS_DUCKDB_PATH": str(database)},
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"local dbt build failed:\n{(result.stdout + result.stderr)[-4000:]}")


def _evidence(database: Path) -> dict[str, object]:
    with duckdb.connect(str(database), read_only=True) as connection:
        return {
            "customers": connection.execute("select count(*) from mart_customer_360").fetchone()[0],
            "renewals": connection.execute("select count(*) from mart_renewal_pipeline").fetchone()[
                0
            ],
            "invoice_1": [
                str(value)
                for value in connection.execute(
                    "select invoice_date, amount from fct_invoices where invoice_id = 'I00001'"
                ).fetchone()
            ],
            "invoice_duplicates": connection.execute(
                "select count(*) - count(distinct invoice_id) from fct_invoices"
            ).fetchone()[0],
            "waterfall_violations": connection.execute(
                "select count(*) from mart_mrr_waterfall where "
                "opening_mrr_usd + new_mrr_usd + expansion_mrr_usd + "
                "contraction_mrr_usd + churn_mrr_usd <> closing_mrr_usd"
            ).fetchone()[0],
        }


def run_demo() -> dict[str, object]:
    with TemporaryDirectory(prefix="saas-local-demo-") as directory:
        work = Path(directory)
        database = work / "reference.duckdb"
        initial = generate_batch(work / "deliveries", "2026-10-09", "initial", 17, 12, "normal")
        load_delivery(initial, database)
        _build(database)
        before = _evidence(database)
        correction = generate_batch(
            work / "deliveries", "2026-10-09", "corrected", 17, 13, "late-correction"
        )
        load_delivery(correction, database)
        _build(database)
        after = _evidence(database)
        _build(database)
        replay = _evidence(database)
        if (
            before["customers"] != 12
            or after["customers"] != 13
            or before["invoice_1"] == after["invoice_1"]
            or after != replay
            or after["invoice_duplicates"] != 0
            or after["waterfall_violations"] != 0
        ):
            raise RuntimeError("local replay acceptance conditions failed")
        return {"initial": before, "corrected": after, "replay_identical": True}


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, sort_keys=True))
