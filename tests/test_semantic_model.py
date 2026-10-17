from pathlib import Path

from scripts.validate_semantic_model import validate


def test_inert_semantic_model():
    assert validate() == []


def test_external_source_is_rejected(tmp_path: Path):
    source = Path("fabric/semantic/ExecutiveSaaS.SemanticModel")
    target = tmp_path / source
    import shutil

    shutil.copytree(source, target)
    customer = target / "definition/tables/Customers.tmdl"
    customer.write_text(customer.read_text() + "\n\t\tSnowflake.Databases()\n")
    assert any("external Power Query" in error for error in validate(tmp_path))
