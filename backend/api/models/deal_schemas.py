"""Pydantic models for deal configuration and term sheet generation."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


class DealConfig(BaseModel):
    """Full deal specification for term sheet generation."""

    # Economic Terms
    currency: str = "USD"
    investment_amount: float
    pre_money_valuation: Optional[float] = None
    post_money_valuation: Optional[float] = None
    price_per_share: Optional[float] = None

    # Round/Instrument
    round_type: str = "Seed"  # Seed, Series A, Series B, etc.
    instrument_type: str = "CCPS"  # CCPS, Equity, SAFE, CCD
    securities: Optional[str] = None

    # Board Composition
    board_size: Optional[int] = None
    investor_board_seats: int = 0
    founder_board_seats: Optional[int] = None
    independent_board_seats: Optional[int] = None
    observer_seats: Optional[int] = None

    # ESOP/Option Pool
    option_pool_percent: Optional[float] = None
    option_pool_timing: str = "pre"  # "pre" or "post" money

    # Key Protections
    liquidation_preference_multiple: Optional[float] = None
    liquidation_preference_participation: Optional[str] = None  # "non_participating", "participating", "participating_with_cap"
    anti_dilution_type: Optional[str] = None  # "none", "broad_wa", "narrow_wa", "full_ratchet"
    reserved_matters_scope: Optional[str] = None  # "narrow_list", "market_list", "broad_list"

    # Transfer Rights
    rofr_days: Optional[int] = None
    tag_along_type: Optional[str] = None  # "none", "pro_rata_only", "full_on_threshold"
    drag_along_years: Optional[int] = None

    # Other
    exclusivity_days: Optional[int] = None
    information_rights_level: Optional[str] = None
    preemptive_rights_scope: Optional[str] = None  # "none", "limited_next_round", "full_ongoing"

    @model_validator(mode="after")
    def validate_post_money(self) -> "DealConfig":
        """Calculate post_money_valuation if not provided."""
        if self.post_money_valuation is None and self.pre_money_valuation is not None:
            self.post_money_valuation = self.pre_money_valuation + self.investment_amount
        return self

    @field_validator("liquidation_preference_participation")
    @classmethod
    def validate_participation(cls, v: Optional[str]) -> Optional[str]:
        """Validate participation type."""
        if v is not None and v not in ["non_participating", "participating", "participating_with_cap"]:
            raise ValueError(f"Invalid participation type: {v}")
        return v

    @field_validator("anti_dilution_type")
    @classmethod
    def validate_anti_dilution(cls, v: Optional[str]) -> Optional[str]:
        """Validate anti-dilution type."""
        if v is not None and v not in ["none", "broad_wa", "narrow_wa", "full_ratchet"]:
            raise ValueError(f"Invalid anti-dilution type: {v}")
        return v

    @field_validator("option_pool_timing")
    @classmethod
    def validate_pool_timing(cls, v: str) -> str:
        """Validate option pool timing."""
        if v not in ["pre", "post"]:
            raise ValueError(f"Invalid option pool timing: {v}")
        return v

    @field_validator("instrument_type")
    @classmethod
    def validate_instrument(cls, v: str) -> str:
        """Validate instrument type."""
        if v not in ["CCPS", "Equity", "SAFE", "CCD"]:
            raise ValueError(f"Invalid instrument type: {v}")
        return v


class DealOverrides(BaseModel):
    """Partial user input - all fields optional."""

    # Economic Terms
    currency: Optional[str] = None
    investment_amount: Optional[float] = None
    pre_money_valuation: Optional[float] = None
    post_money_valuation: Optional[float] = None
    price_per_share: Optional[float] = None

    # Round/Instrument
    round_type: Optional[str] = None
    instrument_type: Optional[str] = None
    securities: Optional[str] = None

    # Board Composition
    board_size: Optional[int] = None
    investor_board_seats: Optional[int] = None
    founder_board_seats: Optional[int] = None
    independent_board_seats: Optional[int] = None
    observer_seats: Optional[int] = None

    # ESOP/Option Pool
    option_pool_percent: Optional[float] = None
    option_pool_timing: Optional[str] = None

    # Key Protections
    liquidation_preference_multiple: Optional[float] = None
    liquidation_preference_participation: Optional[str] = None
    anti_dilution_type: Optional[str] = None
    reserved_matters_scope: Optional[str] = None

    # Transfer Rights
    rofr_days: Optional[int] = None
    tag_along_type: Optional[str] = None
    drag_along_years: Optional[int] = None

    # Other
    exclusivity_days: Optional[int] = None
    information_rights_level: Optional[str] = None
    preemptive_rights_scope: Optional[str] = None


def get_base_deal_config() -> DealConfig:
    """Return market-standard default deal configuration."""
    return DealConfig(
        currency="USD",
        investment_amount=0.0,  # Must be overridden
        round_type="Seed",
        instrument_type="CCPS",
        investor_board_seats=0,
        option_pool_timing="pre",
        # Market defaults from bands.json "market" bands
        liquidation_preference_multiple=1.0,
        liquidation_preference_participation="non_participating",
        anti_dilution_type="broad_wa",
        exclusivity_days=45,
        tag_along_type="pro_rata_only",
        preemptive_rights_scope="limited_next_round",
        reserved_matters_scope="market_list",
    )

