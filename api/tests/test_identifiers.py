import pytest

from app.identifiers import (
    IdentifierError,
    is_placeholder_gene_id,
    is_valid_disease_id,
    is_valid_gene_id,
    validate_association,
)


def test_valid_gene_and_disease_ids():
    assert is_valid_gene_id("ENSG00000012048")
    assert not is_valid_gene_id("ENSGABC")
    assert is_valid_disease_id("MONDO_0007254")
    assert is_valid_disease_id("EFO_0000305")
    assert not is_valid_disease_id("breast cancer")


def test_placeholder_detection():
    assert is_placeholder_gene_id("OT1234")
    assert is_placeholder_gene_id("GENE42")
    assert not is_placeholder_gene_id("ENSG00000012048")


def test_validate_association_warns_but_not_strict_for_placeholder():
    row = {"target_id": "GENE42", "disease_id": "MONDO_0007254"}
    warnings = validate_association(row, strict=True)
    assert any("placeholder" in w for w in warnings)


def test_validate_association_strict_raises_on_bad_disease():
    row = {"target_id": "ENSG00000012048", "disease_id": "not-an-ontology-id"}
    with pytest.raises(IdentifierError):
        validate_association(row, strict=True)


def test_validate_association_non_strict_collects_warnings():
    row = {"target_id": "xyz", "disease_id": "bad"}
    warnings = validate_association(row, strict=False)
    assert len(warnings) == 2
