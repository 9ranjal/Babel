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


def test_extract_liquidation_multiple_and_participation():
    attrs = extract_attributes("Series A includes a 2.0x participating liquidation preference.")
    assert attrs.get("liq_multiple") == 2.0
    assert attrs.get("participation") == "participating"


def test_extract_antidilution_type():
    attrs = extract_attributes("Anti-dilution protection shall be broad-based weighted average.")
    assert attrs.get("antidilution_type") == "broad-based"


def test_extract_option_pool_percent():
    attrs = extract_attributes("Option pool will be topped up to 15% post-money.")
    assert attrs.get("pool_percent") == 15.0


def test_extract_vesting_and_cliff():
    attrs = extract_attributes("Founders vest over 4 years with a 12 month cliff in reverse vesting.")
    assert attrs.get("vesting_years") == 4
    assert attrs.get("cliff_months") == 12


