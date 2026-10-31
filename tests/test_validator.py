import pytest
from pydantic import ValidationError

from data_pipeline.validator import ASINRecord, PriceRecord, SellerRecord


def test_asin_record_accepts_valid_asin():
    record = ASINRecord(asin="b012345678")
    assert record.asin == "B012345678"


def test_asin_record_rejects_invalid_asin():
    with pytest.raises(ValidationError):
        ASINRecord(asin="short")


def test_price_record_rejects_non_positive_price():
    with pytest.raises(ValidationError):
        PriceRecord(asin="B012345678", seller_name="Seller", price=0)


def test_seller_record_requires_name():
    with pytest.raises(ValidationError):
        SellerRecord(seller_name="   ")

