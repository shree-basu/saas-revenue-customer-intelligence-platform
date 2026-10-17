"""Offline guard against making the design-only Fabric item executable."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.validate_fabric_artifacts import ROOT, validate_mirror, validate_pipeline


def test_fail_closed_pipeline_contract() -> None:
    assert validate_pipeline() == []


def test_copy_activity_cannot_be_added_without_review(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "fabric", tmp_path / "fabric")
    path = tmp_path / "fabric/pipelines/FinanceTargets.DataPipeline/pipeline-content.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    content["properties"]["activities"].append({"name": "UnsafeCopy", "type": "Copy"})
    path.write_text(json.dumps(content), encoding="utf-8")
    assert any("fail-closed" in message for message in validate_pipeline(tmp_path))


def test_connection_reference_is_rejected(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "fabric", tmp_path / "fabric")
    path = tmp_path / "fabric/pipelines/FinanceTargets.DataPipeline/pipeline-content.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    content["properties"]["activities"][0]["externalReferences"] = {
        "connection": "00000000-0000-0000-0000-000000000000"
    }
    path.write_text(json.dumps(content), encoding="utf-8")
    assert any("connections" in message for message in validate_pipeline(tmp_path))


def test_mirror_has_only_certified_marts_and_no_real_connection() -> None:
    assert validate_mirror() == []


def test_mirror_all_tables_is_rejected(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "fabric", tmp_path / "fabric")
    path = tmp_path / "fabric/mirroring/CertifiedMarts.MirroredDatabase/mirroring.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    del content["properties"]["mountedTables"]
    path.write_text(json.dumps(content), encoding="utf-8")
    assert any("explicitly select" in message for message in validate_mirror(tmp_path))


def test_real_mirror_connection_is_rejected(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "fabric", tmp_path / "fabric")
    path = tmp_path / "fabric/mirroring/CertifiedMarts.MirroredDatabase/mirroring.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    content["properties"]["source"]["typeProperties"]["connection"] = (
        "11111111-1111-1111-1111-111111111111"
    )
    path.write_text(json.dumps(content), encoding="utf-8")
    assert any("zero connection" in message for message in validate_mirror(tmp_path))
