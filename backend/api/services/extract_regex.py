from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Core taxonomy patterns
PATTERNS: Dict[str, re.Pattern[str]] = {
    "exclusivity": re.compile(r"\b(exclusivity|no[- ]?shop|no solicitation)\b", re.I),
    "rofo": re.compile(r"\b(right of first offer|rofo)\b", re.I),
    "rofr": re.compile(r"\b(right of first refusal|rofr)\b", re.I),
    "tag": re.compile(r"\b(tag[- ]?along)\b", re.I),
    "drag": re.compile(r"\b(drag[- ]?along)\b", re.I),
    "anti_dilution": re.compile(r"\b(anti[- ]?dilution|price protection)\b", re.I),
    "preemption": re.compile(r"\b(pre[- ]?empt(ive|ion)|pro[- ]?rata)\b", re.I),
    "vesting_clawback": re.compile(r"\b(vesting|claw[- ]?back)\b", re.I),
    "exit": re.compile(r"\b(exit|qipo|liquidity event)\b", re.I),
    # Expanded buckets commonly present in term sheets
    "board_composition": re.compile(r"\b(board (composition|of directors)|board seats?)\b", re.I),
    "information_rights": re.compile(r"\b(information rights?|reporting)\b", re.I),
    "liquidation_preference": re.compile(r"\b(liquidation preference|liq pref)\b", re.I),
    "option_pool": re.compile(r"\b(option pool|employee option|esop)\b", re.I),
    "protective_provisions": re.compile(r"\b(protective provisions?)\b", re.I),
    "dividends": re.compile(r"\b(dividends?)\b", re.I),
    "participation": re.compile(r"\b(participation (rights?)?)\b", re.I),
    "valuation_terms": re.compile(r"\b(valuation|pre[- ]?money|post[- ]?money|price per share)\b", re.I),
    "confidentiality": re.compile(r"\b(confidentiality|non[- ]?disclosure|nda)\b", re.I),
    "non_solicitation": re.compile(r"\b(non[- ]?solicit(ation)?)\b", re.I),
}

# Heading aliases to map headings to clause keys
BUCKET_ALIASES: Dict[str, re.Pattern[str]] = {
    "drag": re.compile(r"\bdrag[ -]?along\b", re.I),
    "tag": re.compile(r"\btag[ -]?along\b", re.I),
    "rofo": re.compile(r"\bright of first offer\b|\brofo\b", re.I),
    "rofr": re.compile(r"\bright of first refusal\b|\brofr\b", re.I),
    "exclusivity": re.compile(r"\bexclusivit(y|ies)\b|\bno[ -]?shop\b", re.I),
    "board_composition": re.compile(r"\b(board of directors|board composition|board seat)\b", re.I),
    "information_rights": re.compile(r"\binformation rights?\b|\breporting\b", re.I),
    "liquidation_preference": re.compile(r"\bliquidation preference\b|\bliq pref\b", re.I),
    "option_pool": re.compile(r"\boption pool\b|\besop\b", re.I),
    "protective_provisions": re.compile(r"\bprotective provisions?\b", re.I),
    "dividends": re.compile(r"\bdividends?\b", re.I),
    "participation": re.compile(r"\bparticipation\b", re.I),
    "valuation_terms": re.compile(r"\b(pre[- ]?money|post[- ]?money|valuation|price per share)\b", re.I),
    "confidentiality": re.compile(r"\b(confidentiality|non[- ]?disclosure|nda)\b", re.I),
    "non_solicitation": re.compile(r"\bnon[- ]?solicit(ation)?\b", re.I),
    "preemption": re.compile(r"\b(pre[- ]?empt(ive|ion)|pro[- ]?rata)\b", re.I),
    "anti_dilution": re.compile(r"\b(anti[- ]?dilution|price protection)\b", re.I),
    "vesting_clawback": re.compile(r"\b(vesting|claw[- ]?back)\b", re.I),
    "exit": re.compile(r"\b(exit|qipo|liquidity event)\b", re.I),
}


def _paragraphs(text: str) -> List[tuple[int, int, str]]:
    paras: List[tuple[int, int, str]] = []
    start = 0
    for block in text.split("\n\n"):
        block_stripped = block.strip()
        if not block_stripped:
            start += len(block) + 2
            continue
        end = start + len(block)
        paras.append((start, end, block_stripped))
        start = end + 2
    return paras


def regex_extract(text: str) -> List[Dict]:
    results: List[Dict] = []
    for p_start, p_end, para in _paragraphs(text):
        for key, pattern in PATTERNS.items():
            if pattern.search(para):
                results.append(
                    {
                        "clause_key": key,
                        "title": key.replace("_", " ").title(),
                        "text": para,
                        "start_idx": p_start,
                        "end_idx": p_end,
                        "page_hint": None,
                        "attributes": {},
                        "confidence": 0.6,
                    }
                )
                break
    return results


def _parse_amount(raw: str) -> Optional[float]:
    s = raw.strip().upper().replace(",", "").replace("USD", "").replace("GBP", "").replace("£", "").replace("$", "")
    m = re.search(r"([\\d]+(?:\\.\\d+)?)\\s*([KM]?)", s)
    if not m:
        return None
    num = float(m.group(1))
    suffix = m.group(2)
    if suffix == "K":
        num *= 1_000
    elif suffix == "M":
        num *= 1_000_000
    return num


def extract_attributes(text: str) -> Dict[str, Any]:
    attrs: Dict[str, Any] = {}
    m_pct = re.search(r"(\\d{1,3})\\s*%", text)
    if m_pct:
        try:
            attrs["percent"] = int(m_pct.group(1))
        except Exception:
            pass
    m_days = re.search(r"(\\d{1,4})\\s+day(s)?\\b", text, flags=re.I)
    if m_days:
        try:
            attrs["days"] = int(m_days.group(1))
        except Exception:
            pass
    m_amt = re.search(r"(\\$|£|USD|GBP)\\s*[\\d,]+(?:\\.\\d+)?\\s*[kmKM]?", text)
    if not m_amt:
        m_amt = re.search(r"\\b[\\d,]+(?:\\.\\d+)?\\s*[kmKM]\\b", text)
    if m_amt:
        val = _parse_amount(m_amt.group(0))
        if val is not None:
            attrs["amount"] = float(val)
    return attrs

