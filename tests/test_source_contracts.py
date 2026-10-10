"""Tests for immutable source identity and tamper detection."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from data.contracts import ContractViolation, validate_delivery
from data.generate_saas_batch import generate_batch


@pytest.fixture
def delivery(tmp_path: Path) -> Path:
    return generate_batch(tmp_path, "2026-10-09", "test-1", 17, 5, "normal")


def test_deterministic_bytes_across_distinct_roots(tmp_path: Path) -> None:
    first = generate_batch(tmp_path / "one", "2026-10-09", "same", 17, 5, "normal")
    second = generate_batch(tmp_path / "two", "2026-10-09", "same", 17, 5, "normal")
    assert {p.relative_to(first): p.read_bytes() for p in first.rglob("*") if p.is_file()} == {
        p.relative_to(second): p.read_bytes() for p in second.rglob("*") if p.is_file()
    }
    assert len(validate_delivery(first)["files"]) == 8


def test_regeneration_refused(delivery: Path) -> None:
    with pytest.raises(ContractViolation, match="immutable"):
        generate_batch(delivery.parents[1], "2026-10-09", "test-1", 17, 5, "normal")


@pytest.mark.parametrize("file_name", ["manifest.json", "_SUCCESS", "crm/accounts.csv"])
def test_missing_file(delivery: Path, file_name: str) -> None:
    (delivery / file_name).unlink()
    with pytest.raises(ContractViolation):
        validate_delivery(delivery)


def test_extra_file(delivery: Path) -> None:
    (delivery / "unexpected.csv").write_text("x\n", encoding="utf-8")
    with pytest.raises(ContractViolation, match="extra"):
        validate_delivery(delivery)


def test_path_redirect(delivery: Path) -> None:
    manifest_path = delivery / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["relative_path"] = "../other.csv"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ContractViolation, match="inventory"):
        validate_delivery(delivery)


def test_checksum_mismatch(delivery: Path) -> None:
    with (delivery / "crm/accounts.csv").open("a", encoding="utf-8") as handle:
        handle.write("tamper\n")
    with pytest.raises(ContractViolation, match="checksum"):
        validate_delivery(delivery)


def test_row_count_mismatch(delivery: Path) -> None:
    manifest_path = delivery / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["row_count"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ContractViolation, match="row count"):
        validate_delivery(delivery)


def test_schema_mismatch(delivery: Path) -> None:
    manifest_path = delivery / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["columns"][0] = "wrong_column"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ContractViolation, match="schema"):
        validate_delivery(delivery)


@pytest.mark.parametrize("scenario", ["duplicate-record", "orphan-reference", "invalid-domain"])
def test_failure_scenarios(tmp_path: Path, scenario: str) -> None:
    path = generate_batch(tmp_path, "2026-10-09", scenario, 17, 5, scenario)
    with pytest.raises(ContractViolation):
        validate_delivery(path)


def test_modified_existing_delivery(delivery: Path) -> None:
    with (delivery / "billing/invoices.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    rows[1][-2] = "2026-10-08"
    with (delivery / "billing/invoices.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    with pytest.raises(ContractViolation, match="checksum"):
        validate_delivery(delivery)
