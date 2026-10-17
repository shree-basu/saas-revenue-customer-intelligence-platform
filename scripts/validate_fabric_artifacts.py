"""Static, offline validation of deliberately inert Fabric design artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "fabric/pipelines/FinanceTargets.DataPipeline"
SENTINEL_LOGICAL_ID = "e7b6a15c-38bb-5b82-9122-6472df105d11"
MIRROR_LOGICAL_ID = "5a972edd-c3c0-56df-a33d-cf2ed09c83a0"
ZERO_CONNECTION = "00000000-0000-0000-0000-000000000000"
CERTIFIED_MARTS = {
    "MART_CUSTOMER_360",
    "MART_MRR_WATERFALL",
    "MART_RENEWAL_PIPELINE",
    "MART_REVENUE_RETENTION",
    "MART_REVENUE_VS_TARGET",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_key(value: object, banned: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in banned or _has_key(child, banned) for key, child in value.items())
    if isinstance(value, list):
        return any(_has_key(child, banned) for child in value)
    return False


def validate_pipeline(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    folder = root / PIPELINE.relative_to(ROOT)
    try:
        platform = _read(folder / ".platform")
        content = _read(folder / "pipeline-content.json")
        contract = _read(root / "fabric/contracts/finance-targets.json")
    except (OSError, ValueError) as exc:
        return [f"missing or invalid Fabric pipeline artifact: {exc}"]
    if (
        platform.get("version") != "2.0"
        or platform.get("metadata", {}).get("type") != "DataPipeline"
    ):
        errors.append("pipeline platform format/type differs from documented v2 shape")
    if platform.get("config", {}).get("logicalId") != SENTINEL_LOGICAL_ID:
        errors.append("pipeline logical ID changed")
    if {path.name for path in folder.iterdir()} != {".platform", "pipeline-content.json"}:
        errors.append("pipeline item contains unexpected files")
    if _has_key(content, {"connection", "externalReferences", "triggers", "schedule"}):
        errors.append("pipeline must not reference connections or triggers")
    activities = content.get("properties", {}).get("activities")
    if not isinstance(activities, list) or len(activities) != 1:
        errors.append("pipeline must contain exactly one fail-closed activity")
    elif (
        activities[0].get("type") != "Fail"
        or activities[0].get("typeProperties", {}).get("errorCode")
        != "NO_APPROVED_CLOUD_CONNECTION"
    ):
        errors.append("pipeline fail-closed activity changed")
    if contract.get("status") != "design_only_no_connection":
        errors.append("finance target contract must remain design-only")
    if contract.get("business_key") != ["target_month", "region", "segment"]:
        errors.append("finance target grain changed")
    if contract.get("target_logical_table") != "RAW.SALES_TARGETS":
        errors.append("finance target boundary changed")
    return errors


def validate_mirror(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    folder = root / "fabric/mirroring/CertifiedMarts.MirroredDatabase"
    try:
        platform = _read(folder / ".platform")
        content = _read(folder / "mirroring.json")
    except (OSError, ValueError) as exc:
        return [f"missing or invalid Fabric mirror artifact: {exc}"]
    if {path.name for path in folder.iterdir()} != {".platform", "mirroring.json"}:
        errors.append("mirror item contains unexpected files")
    if (
        platform.get("version") != "2.0"
        or platform.get("metadata", {}).get("type") != "MirroredDatabase"
    ):
        errors.append("mirror platform format/type changed")
    if platform.get("config", {}).get("logicalId") != MIRROR_LOGICAL_ID:
        errors.append("mirror logical ID changed")
    properties = content.get("properties", {})
    source = properties.get("source", {})
    source_properties = source.get("typeProperties", {})
    if source.get("type") != "Snowflake" or source_properties != {
        "connection": ZERO_CONNECTION,
        "database": "SAAS_EXAMPLE_DB",
    }:
        errors.append("mirror must retain fictional Snowflake source and zero connection")
    target = properties.get("target", {})
    if target.get("type") != "MountedRelationalDatabase" or target.get("typeProperties") != {
        "defaultSchema": "MARTS",
        "format": "Delta",
        "retentionInDays": 7,
    }:
        errors.append("mirror target contract changed")
    mounted = properties.get("mountedTables")
    if not isinstance(mounted, list) or len(mounted) != len(CERTIFIED_MARTS):
        errors.append("mirror must explicitly select only five certified marts")
    else:
        actual = {
            (
                table.get("source", {}).get("typeProperties", {}).get("schemaName"),
                table.get("source", {}).get("typeProperties", {}).get("tableName"),
            )
            for table in mounted
        }
        if actual != {("MARTS", name) for name in CERTIFIED_MARTS}:
            errors.append("mirror mounted-table allowlist changed")
    if set(properties) != {"source", "target", "mountedTables"}:
        errors.append("mirror contains unexpected properties")
    return errors


if __name__ == "__main__":
    failures = validate_pipeline() + validate_mirror()
    if failures:
        raise SystemExit("\n".join(failures))
    print("Fabric static contracts passed; no real connection or execution")
