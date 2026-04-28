import pytest
from pydantic import ValidationError

from backend.interface.schemas.data_contract import DataContractCreateModel


def test_valid_create_model():
    m = DataContractCreateModel(
        title="Orders",
        owner="alice",
        domain="commerce",
        tier=2,
    )
    assert m.version == "1.0.0"
    assert m.status == "draft"
    assert m.models.fields == []


def test_tier_below_range_rejected():
    with pytest.raises(ValidationError):
        DataContractCreateModel(title="x", owner="o", domain="d", tier=0)


def test_tier_above_range_rejected():
    with pytest.raises(ValidationError):
        DataContractCreateModel(title="x", owner="o", domain="d", tier=5)


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        DataContractCreateModel(title="x", owner="o", domain="d", tier=1, status="unknown")


def test_schema_field_defaults():
    m = DataContractCreateModel(title="x", owner="o", domain="d", tier=3)
    assert m.servicelevels.freshness == ""
    assert m.servicelevels.availability == ""
