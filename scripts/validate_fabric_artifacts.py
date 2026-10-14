"""Static, offline validation of deliberately inert Fabric design artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "fabric/pipelines/FinanceTargets.DataPipeline"
SENTINEL_LOGICAL_ID = "e7b6a15c-38bb-5b82-9122-6472df105d11"


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


if __name__ == "__main__":
    failures = validate_pipeline()
    if failures:
        raise SystemExit("\n".join(failures))
    print("Fabric pipeline static contract passed; no connection or execution")
