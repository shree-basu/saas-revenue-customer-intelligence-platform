"""Cloud-free verification of one immutable source delivery."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

SCHEMA_VERSION = 1
SOURCES: dict[str, dict[str, tuple[str, ...]]] = {
    "crm": {
        "accounts": (
            "account_id",
            "account_name",
            "segment",
            "industry",
            "region",
            "country",
            "sales_owner",
            "customer_success_manager",
            "account_status",
            "created_at",
            "updated_at",
        )
    },
    "billing": {
        "subscriptions": (
            "subscription_id",
            "account_id",
            "product_id",
            "plan_id",
            "subscription_start_date",
            "subscription_end_date",
            "billing_frequency",
            "quantity",
            "contract_value",
            "currency",
            "subscription_status",
            "renewal_date",
            "updated_at",
        ),
        "invoices": (
            "invoice_id",
            "account_id",
            "subscription_id",
            "invoice_date",
            "due_date",
            "amount",
            "currency",
            "payment_status",
            "paid_date",
            "updated_at",
        ),
    },
    "product": {
        "product_usage_daily": (
            "account_id",
            "product_id",
            "usage_date",
            "active_users",
            "licensed_users",
            "sessions",
            "api_calls",
            "failed_requests",
            "usage_minutes",
            "updated_at",
        )
    },
    "support": {
        "support_cases": (
            "case_id",
            "account_id",
            "opened_at",
            "closed_at",
            "severity",
            "category",
            "status",
            "sla_breached",
            "resolution_minutes",
            "updated_at",
        )
    },
    "finance": {
        "sales_targets": (
            "target_month",
            "region",
            "segment",
            "arr_target",
            "new_arr_target",
            "renewal_target",
            "updated_at",
        )
    },
    "reference": {
        "products": ("product_id", "product_name", "product_family", "active"),
        "plans": ("plan_id", "plan_name", "billing_frequency", "active"),
    },
}


class ContractViolation(ValueError):
    """A delivery cannot be trusted for ingestion."""


def expected_files() -> dict[str, tuple[str, ...]]:
    return {
        f"{source}/{entity}.csv": columns
        for source, entities in SOURCES.items()
        for entity, columns in entities.items()
    }


def delivery_path(root: Path, business_date: str, batch_id: str) -> Path:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", business_date):
        raise ContractViolation("business_date must be YYYY-MM-DD")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", batch_id):
        raise ContractViolation("unsafe batch_id")
    return root / f"business_date={business_date}" / f"batch_id={batch_id}"


def _assert_unique(rows: list[dict[str, str]], keys: tuple[str, ...], entity: str) -> None:
    values = [tuple(row[key] for key in keys) for row in rows]
    if any(not all(parts) for parts in values) or len(values) != len(set(values)):
        raise ContractViolation(f"blank or duplicate {entity} grain: {keys}")


def validate_delivery(path: Path) -> dict:
    """Validate identity, exact file set, counts, hashes, schemas and source grains."""
    if (
        not path.is_dir()
        or not (path / "_SUCCESS").is_file()
        or not (path / "manifest.json").is_file()
    ):
        raise ContractViolation("delivery, manifest or _SUCCESS missing")
    if any(item.is_symlink() for item in path.rglob("*")):
        raise ContractViolation("symlink in delivery")
    try:
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractViolation("invalid manifest") from exc
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ContractViolation("schema version mismatch")
    expected_path = delivery_path(
        path.parents[1], manifest.get("business_date", ""), manifest.get("batch_id", "")
    )
    if path.resolve() != expected_path.resolve():
        raise ContractViolation("delivery path does not match manifest identity")
    expected = expected_files()
    actual = {item.relative_to(path).as_posix() for item in path.rglob("*") if item.is_file()}
    if actual != set(expected) | {"manifest.json", "_SUCCESS"}:
        raise ContractViolation("missing or extra delivery file")
    entries = manifest.get("files")
    if (
        not isinstance(entries, list)
        or {entry.get("relative_path") for entry in entries} != set(expected)
        or len(entries) != len(expected)
    ):
        raise ContractViolation("manifest file inventory mismatch")
    parsed: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        relative = entry["relative_path"]
        source, entity_file = relative.split("/")
        entity = entity_file.removesuffix(".csv")
        if (entry.get("source"), entry.get("entity"), entry.get("format")) != (
            source,
            entity,
            "csv",
        ):
            raise ContractViolation(f"source metadata mismatch: {relative}")
        if entry.get("columns") != list(expected[relative]):
            raise ContractViolation(f"manifest schema mismatch: {relative}")
        raw = (path / relative).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
            raise ContractViolation(f"checksum mismatch: {relative}")
        with (path / relative).open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != expected[relative]:
                raise ContractViolation(f"CSV schema mismatch: {relative}")
            rows = list(reader)
        if type(entry.get("row_count")) is not int or entry["row_count"] != len(rows):
            raise ContractViolation(f"row count mismatch: {relative}")
        parsed[entity] = rows
    for entity, keys in {
        "accounts": ("account_id",),
        "subscriptions": ("subscription_id",),
        "invoices": ("invoice_id",),
        "product_usage_daily": ("account_id", "product_id", "usage_date"),
        "support_cases": ("case_id",),
        "sales_targets": ("target_month", "region", "segment"),
        "products": ("product_id",),
        "plans": ("plan_id",),
    }.items():
        _assert_unique(parsed[entity], keys, entity)
    account_ids = {row["account_id"] for row in parsed["accounts"]}
    subscription_ids = {row["subscription_id"] for row in parsed["subscriptions"]}
    for entity in ("subscriptions", "invoices", "product_usage_daily", "support_cases"):
        if any(row["account_id"] not in account_ids for row in parsed[entity]):
            raise ContractViolation(f"orphan account reference in {entity}")
    if any(row["subscription_id"] not in subscription_ids for row in parsed["invoices"]):
        raise ContractViolation("orphan subscription reference")
    if any(row["account_status"] not in {"ACTIVE", "INACTIVE"} for row in parsed["accounts"]):
        raise ContractViolation("invalid account status")
    return manifest
