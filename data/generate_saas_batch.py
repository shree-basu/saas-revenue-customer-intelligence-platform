"""Deterministic synthetic SaaS batch generator; no network or cloud client."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from datetime import date, timedelta
from pathlib import Path

from data.contracts import SCHEMA_VERSION, SOURCES, ContractViolation, delivery_path

SCENARIOS = (
    "normal",
    "duplicate-record",
    "orphan-reference",
    "invalid-domain",
    "late-correction",
    "account-correction",
)


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def generate_batch(
    output_root: Path,
    business_date: str,
    batch_id: str,
    seed: int,
    accounts: int,
    scenario: str,
) -> Path:
    if scenario not in SCENARIOS or accounts < 2 or seed < 0:
        raise ContractViolation("unsupported scenario, account count or seed")
    day = date.fromisoformat(business_date)
    target = delivery_path(output_root, business_date, batch_id)
    if target.exists():
        raise ContractViolation("immutable delivery already exists")
    timestamp = f"{day.isoformat()}T00:00:00Z"
    regions = ("AMER", "EMEA", "APAC")
    segments = ("SMB", "MID_MARKET", "ENTERPRISE")
    account_rows = []
    subscription_rows = []
    monthly_state_rows = []
    invoice_rows = []
    usage_rows = []
    support_rows = []
    current_month = day.replace(day=1)
    prior_month = (current_month - timedelta(days=1)).replace(day=1)
    for index in range(1, accounts + 1):
        account_id = f"A{index:05d}"
        subscription_id = f"S{index:05d}"
        product_id = f"P{1 + (index + seed) % 2}"
        region = regions[(index + seed) % 3]
        segment = segments[(index + seed // 3) % 3]
        account_rows.append(
            {
                "account_id": account_id,
                "account_name": f"Synthetic Customer {index}",
                "segment": segment,
                "industry": "SOFTWARE",
                "region": region,
                "country": {"AMER": "US", "EMEA": "GB", "APAC": "IN"}[region],
                "sales_owner": f"Synthetic Seller {index % 4}",
                "customer_success_manager": f"Synthetic CSM {index % 3}",
                "account_status": "ACTIVE",
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )
        base_annual = 1200 + index * 120 + seed % 19
        movement = index % 5
        prior_annual = 0 if movement == 1 else base_annual
        current_annual = {
            1: base_annual,
            2: base_annual + 120,
            3: base_annual - 120,
            4: 0,
            0: base_annual,
        }[movement]
        current_status = "CANCELLED" if current_annual == 0 else "ACTIVE"
        # Give the local renewal mart real near-term cases without shortening
        # the annual contract. Other subscriptions remain outside 90 days.
        contract_age_days = 305 if index % 3 == 0 else 90
        renewal_date = day + timedelta(days=365 - contract_age_days)
        for month, annual_value in ((prior_month, prior_annual), (current_month, current_annual)):
            monthly_state_rows.append(
                {
                    "subscription_id": subscription_id,
                    "account_id": account_id,
                    "product_id": product_id,
                    "state_month": month.isoformat(),
                    "billing_frequency": "ANNUAL",
                    "quantity": 5 + index % 8,
                    "contract_value": f"{annual_value:.2f}",
                    "currency": "USD",
                    "subscription_status": (
                        "ACTIVE"
                        if annual_value
                        else "INACTIVE"
                        if month == prior_month
                        else "CANCELLED"
                    ),
                    "updated_at": f"{month.isoformat()}T00:00:00Z",
                }
            )
        subscription_rows.append(
            {
                "subscription_id": subscription_id,
                "account_id": account_id,
                "product_id": product_id,
                "plan_id": "PL_ANNUAL",
                "subscription_start_date": (day - timedelta(days=contract_age_days)).isoformat(),
                "subscription_end_date": renewal_date.isoformat(),
                "billing_frequency": "ANNUAL",
                "quantity": 5 + index % 8,
                "contract_value": f"{current_annual:.2f}",
                "currency": "USD",
                "subscription_status": current_status,
                "renewal_date": renewal_date.isoformat(),
                "updated_at": timestamp,
            }
        )
        invoice_rows.append(
            {
                "invoice_id": f"I{index:05d}",
                "account_id": account_id,
                "subscription_id": subscription_id,
                "invoice_date": day.isoformat(),
                "due_date": (day + timedelta(days=30)).isoformat(),
                "amount": f"{(100 + index * 3):.2f}",
                "currency": "USD",
                "payment_status": "OPEN",
                "paid_date": "",
                "updated_at": timestamp,
            }
        )
        usage_rows.append(
            {
                "account_id": account_id,
                "product_id": product_id,
                "usage_date": day.isoformat(),
                "active_users": 2 + index % 4,
                "licensed_users": 5 + index % 8,
                "sessions": 10 + index,
                "api_calls": 80 + index * 2,
                "failed_requests": index % 3,
                "usage_minutes": 100 + index * 7,
                "updated_at": timestamp,
            }
        )
        support_rows.append(
            {
                "case_id": f"C{index:05d}",
                "account_id": account_id,
                "opened_at": timestamp,
                "closed_at": "",
                "severity": "LOW",
                "category": "HOW_TO",
                "status": "OPEN",
                "sla_breached": "false",
                "resolution_minutes": "",
                "updated_at": timestamp,
            }
        )
    if scenario == "duplicate-record":
        account_rows.append(dict(account_rows[0]))
    elif scenario == "orphan-reference":
        subscription_rows[0]["account_id"] = "A99999"
    elif scenario == "invalid-domain":
        account_rows[0]["account_status"] = "UNKNOWN_STATE"
    elif scenario == "late-correction":
        invoice_rows[0]["invoice_date"] = (day - timedelta(days=35)).isoformat()
        invoice_rows[0]["amount"] = "110.00"
        usage_rows[0]["usage_minutes"] = int(usage_rows[0]["usage_minutes"]) + 11
    elif scenario == "account-correction":
        account_rows[0]["account_name"] = "Synthetic Customer 1 Revised"
        account_rows[0]["updated_at"] = f"{day.isoformat()}T12:00:00Z"
    target_rows = [
        {
            "target_month": day.replace(day=1).isoformat(),
            "region": region,
            "segment": segment,
            "arr_target": "120000.00",
            "new_arr_target": "25000.00",
            "renewal_target": "90.00",
            "updated_at": timestamp,
        }
        for region, segment in sorted({(r["region"], r["segment"]) for r in account_rows})
    ]
    rows_by_entity = {
        "accounts": account_rows,
        "subscriptions": subscription_rows,
        "subscription_monthly_states": monthly_state_rows,
        "invoices": invoice_rows,
        "product_usage_daily": usage_rows,
        "support_cases": support_rows,
        "sales_targets": target_rows,
        "products": [
            {
                "product_id": "P1",
                "product_name": "Analytics",
                "product_family": "CORE",
                "active": "true",
            },
            {
                "product_id": "P2",
                "product_name": "Automation",
                "product_family": "CORE",
                "active": "true",
            },
        ],
        "plans": [
            {
                "plan_id": "PL_ANNUAL",
                "plan_name": "Annual",
                "billing_frequency": "ANNUAL",
                "active": "true",
            },
            {
                "plan_id": "PL_MONTHLY",
                "plan_name": "Monthly",
                "billing_frequency": "MONTHLY",
                "active": "true",
            },
        ],
    }
    target.mkdir(parents=True)
    entries = []
    for source, entities in SOURCES.items():
        (target / source).mkdir()
        for entity, columns in entities.items():
            relative = f"{source}/{entity}.csv"
            payload = _csv_bytes(columns, rows_by_entity[entity])
            (target / relative).write_bytes(payload)
            entries.append(
                {
                    "source": source,
                    "entity": entity,
                    "relative_path": relative,
                    "format": "csv",
                    "columns": list(columns),
                    "row_count": len(rows_by_entity[entity]),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
    manifest = {
        "business_date": business_date,
        "batch_id": batch_id,
        "seed": seed,
        "scenario": scenario,
        "schema_version": SCHEMA_VERSION,
        "generated_at": timestamp,
        "files": entries,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (target / "_SUCCESS").write_text("", encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--business-date", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--accounts", type=int, required=True)
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args()
    print(generate_batch(**vars(arguments)))


if __name__ == "__main__":
    main()
