"""Cloud-free verification of one immutable source delivery."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCHEMA_VERSION = 2
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
        "subscription_monthly_states": (
            "subscription_id",
            "account_id",
            "product_id",
            "state_month",
            "billing_frequency",
            "quantity",
            "contract_value",
            "currency",
            "subscription_status",
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


def _date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ContractViolation(f"invalid date in {label}") from exc


def _timestamp(value: str, label: str) -> None:
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise ContractViolation(f"invalid timestamp in {label}") from exc


def _number(value: str, label: str, *, integral: bool = False) -> Decimal:
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ContractViolation(f"invalid numeric value in {label}") from exc
    if not number.is_finite() or number < 0:
        raise ContractViolation(f"negative or non-finite value in {label}")
    if integral and number != number.to_integral_value():
        raise ContractViolation(f"non-integer value in {label}")
    if not integral and number.as_tuple().exponent < -2:
        raise ContractViolation(f"excessive monetary scale in {label}")
    return number


def _domain(row: dict[str, str], field: str, allowed: set[str], entity: str) -> None:
    if row[field] not in allowed:
        raise ContractViolation(f"invalid {entity}.{field}")


def _check_semantics(parsed: dict[str, list[dict[str, str]]]) -> None:
    product_ids = {row["product_id"] for row in parsed["products"]}
    plan_ids = {row["plan_id"] for row in parsed["plans"]}
    for row in parsed["accounts"]:
        for field, allowed in {
            "account_status": {"ACTIVE", "INACTIVE"},
            "segment": {"SMB", "MID_MARKET", "ENTERPRISE"},
            "region": {"AMER", "EMEA", "APAC"},
        }.items():
            _domain(row, field, allowed, "accounts")
        _timestamp(row["created_at"], "accounts.created_at")
        _timestamp(row["updated_at"], "accounts.updated_at")
    for row in parsed["subscriptions"]:
        for field, allowed in {
            "billing_frequency": {"ANNUAL", "MONTHLY"},
            "subscription_status": {"ACTIVE", "INACTIVE", "CANCELLED"},
            "currency": {"USD"},
        }.items():
            _domain(row, field, allowed, "subscriptions")
        if row["product_id"] not in product_ids or row["plan_id"] not in plan_ids:
            raise ContractViolation("orphan product or plan reference")
        start = _date(row["subscription_start_date"], "subscriptions.start")
        end = _date(row["subscription_end_date"], "subscriptions.end")
        renewal = _date(row["renewal_date"], "subscriptions.renewal")
        if start > end or renewal < start:
            raise ContractViolation("invalid subscription date order")
        _number(row["quantity"], "subscriptions.quantity", integral=True)
        _number(row["contract_value"], "subscriptions.contract_value")
        _timestamp(row["updated_at"], "subscriptions.updated_at")
    subscriptions = {row["subscription_id"]: row for row in parsed["subscriptions"]}
    states_by_subscription: dict[str, list[tuple[date, dict[str, str]]]] = {}
    for row in parsed["subscription_monthly_states"]:
        subscription = subscriptions.get(row["subscription_id"])
        if subscription is None:
            raise ContractViolation("orphan monthly subscription state")
        if (row["account_id"], row["product_id"]) != (
            subscription["account_id"],
            subscription["product_id"],
        ):
            raise ContractViolation("monthly state subscription identity mismatch")
        month = _date(row["state_month"], "subscription_monthly_states.state_month")
        if month.day != 1:
            raise ContractViolation("state_month must be first of month")
        _domain(row, "billing_frequency", {"ANNUAL", "MONTHLY"}, "monthly state")
        _domain(row, "currency", {"USD"}, "monthly state")
        _domain(row, "subscription_status", {"ACTIVE", "INACTIVE", "CANCELLED"}, "monthly state")
        quantity = _number(row["quantity"], "monthly state quantity", integral=True)
        value = _number(row["contract_value"], "monthly state contract_value")
        if quantity <= 0 or (row["subscription_status"] == "ACTIVE") != (value > 0):
            raise ContractViolation("monthly state status/value mismatch")
        _timestamp(row["updated_at"], "monthly state updated_at")
        states_by_subscription.setdefault(row["subscription_id"], []).append((month, row))
    if set(states_by_subscription) != set(subscriptions):
        raise ContractViolation("missing monthly subscription state")
    for subscription_id, states in states_by_subscription.items():
        states.sort(key=lambda item: item[0])
        if len(states) < 2:
            raise ContractViolation("monthly state needs prior and current months")
        for (before, _), (after, _) in zip(states, states[1:], strict=False):
            next_month = (before.replace(day=28) + timedelta(days=4)).replace(day=1)
            if after != next_month:
                raise ContractViolation("monthly state months must be contiguous")
        latest = states[-1][1]
        current = subscriptions[subscription_id]
        if any(
            latest[field] != current[field]
            for field in (
                "account_id",
                "product_id",
                "billing_frequency",
                "quantity",
                "contract_value",
                "currency",
                "subscription_status",
            )
        ):
            raise ContractViolation("monthly latest state differs from subscription current state")
    for row in parsed["invoices"]:
        _domain(row, "currency", {"USD"}, "invoices")
        _domain(row, "payment_status", {"OPEN", "PAID", "OVERDUE", "VOID"}, "invoices")
        invoice_date = _date(row["invoice_date"], "invoices.invoice_date")
        if _date(row["due_date"], "invoices.due_date") < invoice_date:
            raise ContractViolation("invoice due before issue")
        if row["paid_date"]:
            _date(row["paid_date"], "invoices.paid_date")
        if row["payment_status"] == "PAID" and not row["paid_date"]:
            raise ContractViolation("paid invoice lacks paid_date")
        _number(row["amount"], "invoices.amount")
        _timestamp(row["updated_at"], "invoices.updated_at")
    for row in parsed["product_usage_daily"]:
        if row["product_id"] not in product_ids:
            raise ContractViolation("orphan usage product")
        _date(row["usage_date"], "usage.usage_date")
        active = _number(row["active_users"], "usage.active_users", integral=True)
        licensed = _number(row["licensed_users"], "usage.licensed_users", integral=True)
        if active > licensed:
            raise ContractViolation("active users exceed licensed users")
        for field in ("sessions", "api_calls", "failed_requests", "usage_minutes"):
            _number(row[field], f"usage.{field}", integral=True)
        _timestamp(row["updated_at"], "usage.updated_at")
    for row in parsed["support_cases"]:
        _domain(row, "severity", {"LOW", "MEDIUM", "HIGH", "CRITICAL"}, "support_cases")
        _domain(row, "status", {"OPEN", "CLOSED"}, "support_cases")
        _domain(row, "sla_breached", {"true", "false"}, "support_cases")
        _timestamp(row["opened_at"], "support_cases.opened_at")
        if row["closed_at"]:
            _timestamp(row["closed_at"], "support_cases.closed_at")
        if row["resolution_minutes"]:
            _number(row["resolution_minutes"], "support_cases.resolution_minutes", integral=True)
        _timestamp(row["updated_at"], "support_cases.updated_at")
    for row in parsed["sales_targets"]:
        month = _date(row["target_month"], "sales_targets.target_month")
        if month.day != 1:
            raise ContractViolation("target_month must be first of month")
        _domain(row, "region", {"AMER", "EMEA", "APAC"}, "sales_targets")
        _domain(row, "segment", {"SMB", "MID_MARKET", "ENTERPRISE"}, "sales_targets")
        for field in ("arr_target", "new_arr_target", "renewal_target"):
            _number(row[field], f"sales_targets.{field}")
        _timestamp(row["updated_at"], "sales_targets.updated_at")
    for entity in ("products", "plans"):
        for row in parsed[entity]:
            _domain(row, "active", {"true", "false"}, entity)


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
        "subscription_monthly_states": ("subscription_id", "state_month"),
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
    _check_semantics(parsed)
    business_month = date.fromisoformat(manifest["business_date"]).replace(day=1).isoformat()
    if any(row["state_month"] > business_month for row in parsed["subscription_monthly_states"]):
        raise ContractViolation("monthly state after delivery business month")
    if any(
        max(
            row["state_month"]
            for row in parsed["subscription_monthly_states"]
            if row["subscription_id"] == subscription["subscription_id"]
        )
        != business_month
        for subscription in parsed["subscriptions"]
    ):
        raise ContractViolation("latest monthly state must match delivery business month")
    return manifest
