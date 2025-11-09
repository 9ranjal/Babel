from __future__ import annotations

from backend.api.services.extract_regex import extract_attributes


def test_extract_percent():
    attrs = extract_attributes("Dividends at 8% per annum.")
    assert attrs.get("percent") == 8


def test_extract_days():
    attrs = extract_attributes("Notice must be delivered within 30 days of receipt.")
    assert attrs.get("days") == 30


def test_extract_amount_dollars_commas():
    attrs = extract_attributes("The option pool shall be increased by $1,250,000.")
    assert int(attrs.get("amount", 0)) == 1250000


def test_extract_amount_usd_m():
    attrs = extract_attributes("Purchase price is USD 1.5m at close.")
    assert int(attrs.get("amount", 0)) == 1500000


def test_extract_amount_gbp_k():
    attrs = extract_attributes("A break fee of £250k applies.")
    assert int(attrs.get("amount", 0)) == 250000


