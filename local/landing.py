"""Load one validated synthetic delivery into local DuckDB raw tables."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import duckdb

from data.contracts import ContractViolation, validate_delivery


def _check_account_revision_order(connection: duckdb.DuckDBPyConnection, delivery: Path) -> None:
    exists = connection.execute(
        "select count(*) from information_schema.tables "
        "where table_schema = 'raw' and table_name = 'accounts'"
    ).fetchone()[0]
    if not exists:
        return
    previous = connection.execute("select * from raw.accounts")
    columns = [column[0] for column in previous.description]
    prior_rows = {
        row[columns.index("account_id")]: dict(zip(columns, row, strict=True))
        for row in previous.fetchall()
    }
    with (delivery / "crm/accounts.csv").open(newline="", encoding="utf-8") as handle:
        for current in csv.DictReader(handle):
            prior = prior_rows.get(current["account_id"])
            if prior is None:
                continue
            old_time = datetime.fromisoformat(prior["updated_at"])
            new_time = datetime.fromisoformat(current["updated_at"])
            if new_time < old_time:
                raise ContractViolation("out-of-order account revision; rebuild chronologically")
            if new_time == old_time and any(current[key] != prior[key] for key in current):
                raise ContractViolation("changed account row without newer updated_at")


def load_delivery(delivery: Path, database: Path) -> None:
    manifest = validate_delivery(delivery)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database))
    try:
        connection.execute("BEGIN TRANSACTION")
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        _check_account_revision_order(connection, delivery)
        for entry in manifest["files"]:
            entity = entry["entity"]  # allowlisted by validate_delivery
            source = delivery / entry["relative_path"]
            connection.execute(
                f"CREATE OR REPLACE TABLE raw.{entity} AS "
                "SELECT * FROM read_csv(?, header=true, all_varchar=true)",
                [str(source)],
            )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    arguments = parser.parse_args()
    load_delivery(arguments.delivery, arguments.database)


if __name__ == "__main__":
    main()
