"""Load one validated synthetic delivery into local DuckDB raw tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from data.contracts import validate_delivery


def load_delivery(delivery: Path, database: Path) -> None:
    manifest = validate_delivery(delivery)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database))
    try:
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        for entry in manifest["files"]:
            entity = entry["entity"]  # allowlisted by validate_delivery
            source = delivery / entry["relative_path"]
            connection.execute(
                f"CREATE OR REPLACE TABLE raw.{entity} AS "
                "SELECT * FROM read_csv(?, header=true, all_varchar=true)",
                [str(source)],
            )
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
