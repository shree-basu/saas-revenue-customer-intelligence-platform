"""Offline allowlist checks for the inert TMDL reference, not a TMDL/DAX parser."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "fabric/semantic/ExecutiveSaaS.SemanticModel"
EXPECTED = {
    "Customers": {
        "account_id",
        "account_name",
        "region",
        "segment",
        "health_status",
        "reporting_date",
        "current_mrr_usd",
        "overdue_invoice_count",
    },
    "Renewals": {
        "subscription_id",
        "account_id",
        "reporting_date",
        "renewal_date",
        "days_until_renewal",
        "renewal_arr_usd",
    },
    "MRRWaterfall": {
        "reporting_month",
        "opening_mrr_usd",
        "new_mrr_usd",
        "expansion_mrr_usd",
        "contraction_mrr_usd",
        "churn_mrr_usd",
        "closing_mrr_usd",
    },
    "Retention": {"reporting_month", "gross_revenue_retention_pct", "net_revenue_retention_pct"},
    "ARRTargets": {
        "reporting_month",
        "region",
        "segment",
        "actual_arr_usd",
        "target_arr_usd",
        "comparison_status",
    },
}
MEASURES = {
    "Customers": {"Current MRR USD", "Current ARR USD", "At-Risk Accounts"},
    "Renewals": {"Renewal ARR at Risk USD", "Renewing Subscriptions"},
    "MRRWaterfall": {"Opening MRR USD", "Net Movement MRR USD", "Closing MRR USD"},
    "Retention": {"Gross Revenue Retention %", "Net Revenue Retention %"},
    "ARRTargets": {"Actual ARR USD", "Planned ARR USD", "ARR Attainment %"},
}


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    folder = root / MODEL.relative_to(ROOT)
    try:
        pbism = json.loads((folder / "definition.pbism").read_text(encoding="utf-8"))
        database = (folder / "definition/database.tmdl").read_text(encoding="utf-8")
        model = (folder / "definition/model.tmdl").read_text(encoding="utf-8")
        relationships = (folder / "definition/relationships.tmdl").read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        return [f"semantic model files missing or invalid: {exc}"]
    if pbism.get("version") != "5.0" or pbism.get("settings") != {"qnaEnabled": False}:
        errors.append("semantic model definition settings changed")
    if "database ExecutiveSaaS" not in database or "model Model" not in model:
        errors.append("TMDL database/model headers missing")
    if set((folder / "definition/tables").glob("*.tmdl")) != {
        folder / "definition/tables" / f"{name}.tmdl" for name in EXPECTED
    }:
        errors.append("semantic table allowlist changed")
    if not re.fullmatch(
        r"relationship [0-9a-f-]+\s+fromColumn: Renewals\.account_id\s+toColumn: Customers\.account_id\s*",
        relationships,
    ):
        errors.append("semantic relationship changed")
    for name, columns in EXPECTED.items():
        try:
            source = (folder / f"definition/tables/{name}.tmdl").read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(str(exc))
            continue
        if not source.startswith(f"table {name}\n"):
            errors.append(f"{name}: TMDL table header changed")
        actual_columns = set(re.findall(r"^\tcolumn ([a-z_]+)$", source, re.MULTILINE))
        actual_measures = set(re.findall(r"^\tmeasure '([^']+)' =", source, re.MULTILINE))
        if actual_columns != columns or actual_measures != MEASURES[name]:
            errors.append(f"{name}: column/measure allowlist changed")
        if source.count("\tpartition ") != 1 or "\t\tmode: import" not in source:
            errors.append(f"{name}: expected one inert Import partition")
        if "#table(type table [" not in source or "], {})" not in source:
            errors.append(f"{name}: empty local Power Query source changed")
        if re.search(
            r"(?i)\b(snowflake\.databases|lakehouse\.contents|sql\.database|web\.contents)\b",
            source,
        ):
            errors.append(f"{name}: external Power Query source forbidden")
        for table, column in re.findall(r"\b([A-Za-z]+)\[([a-z_]+)\]", source):
            if table not in EXPECTED or column not in EXPECTED[table]:
                errors.append(f"{name}: DAX references unknown {table}[{column}]")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("Inert semantic model structural checks passed; no Power BI execution")
