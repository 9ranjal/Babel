from __future__ import annotations

import re
from typing import Any, Dict, List

from .numbering import strip_leading_numbering
from .sectionizer import sectionize


_CLAUSE_KEY_ORDERED = [
    # Success-list focus
    "company",
    "indian_subsidiary",
    "founders",
    "new_investor",
    "existing_investors",
    "securities",
    "investment_amount",
    "new_investor_ownership",
    "pre_money_valuation",
    "definitive_documents",
    "capitalization",
    "price_per_share",
    "subscription_right",
    "use_of_proceeds",
    "closing_conditions",
    "reps_warranties",
    "existing_shareholder_rights",
    "new_investor_director",
    "shareholders_meetings",
    "reserved_matters",
    "dividend",
    "liquidation_preference",
    "exit_rights",
    "conversion",
    "voting_rights",
    "anti_dilution",
    "registration_rights",
    "preemptive_rights",
    "right_of_first_refusal",
    "tag_along",
    "transfers_by_founders",
    "drag_along",
    "new_investor_transfer_rights",
    "event_of_default",
    "information_inspection_rights",
    "other_rights",
    "non_compete_non_solicit",
    "rights_in_indian_subsidiary",
    "expenses",
    "governing_law",
    "dispute_resolution",
    "counterparts",
    "termination",
    # Legacy/existing keys retained for compatibility
    "parties",
    "valuation",
    "covenants",
    "board",
    "observer",
    "voting",
    "information_rights",
    "audit_rights",
    "anti_dilution",
    "preemptive_pro_rata",
    "rofo",
    "rofr",
    "co_sale",
    "redemption",
    "option_pool",
    "founder_vesting",
    "founder_lockup",
    "transfer_restrictions",
    "pay_to_play",
    "exclusivity",
    "break_fee",
    "confidentiality",
    "notices",
    "costs_expenses",
    "timeline",
    "exit",
]

CLAUSE_KEYS = list(dict.fromkeys(_CLAUSE_KEY_ORDERED))

HEAD_KEYWORDS: Dict[str, List[str]] = {
    # Success list focus
    "company": ["company"],
    "indian_subsidiary": ["indian subsidiary"],
    "founders": ["founders"],
    "new_investor": ["new investor", "investors"],
    "existing_investors": ["existing investors"],
    "investment_amount": [
        "investment amount",
        "subscription amount",
        "aggregate consideration",
        "amount invested",
    ],
    "new_investor_ownership": ["investors' ownership", "new investor ownership"],
    "pre_money_valuation": ["pre-money valuation", "valuation"],
    "definitive_documents": ["definitive documents", "definitive docs"],
    "capitalization": ["capitalization", "shareholding pattern"],
    "price_per_share": ["price per share", "pps", "subscription price"],
    "subscription_right": ["subscription right"],
    "securities": ["securities", "class h preference shares", "instrument", "security"],
    "use_of_proceeds": ["use of proceeds", "application of funds"],
    "closing_conditions": ["conditions precedent", "conditions to closing", "closing conditions"],
    "reps_warranties": ["representations", "warranties", "indemnification"],
    "existing_shareholder_rights": ["existing shareholder rights", "existing investor rights"],
    "new_investor_director": ["investor director", "investor directors"],
    "shareholders_meetings": ["shareholders' meetings", "shareholder meetings"],
    "reserved_matters": [
        "reserved matters",
        "protective provisions",
        "affirmative vote matters",
        "matters requiring consent",
    ],
    "dividend": ["dividend", "dividends", "coupon"],
    "liquidation_preference": ["liquidation preference", "distribution waterfall"],
    "exit_rights": ["exit rights", "exit"],
    "conversion": ["conversion"],
    "voting_rights": ["voting rights", "voting"],
    "anti_dilution": ["anti-dilution", "price protection", "down round protection"],
    "registration_rights": ["registration rights", "registration"],
    "preemptive_rights": ["preemptive rights", "pro rata rights", "pre-emptive rights"],
    # Prefer emitting short-form 'rofr' when explicitly present
    "rofr": ["rofr"],
    "right_of_first_refusal": ["right of first refusal"],
    # Avoid matching generic 'co-sale' here to let 'co_sale' take precedence
    "tag_along": ["tag-along", "tag along"],
    "transfers_by_founders": ["transfers by the founders", "founder transfers", "employment of founders"],
    "drag_along": ["drag-along", "drag along"],
    "new_investor_transfer_rights": ["new investor's right to transfer", "investor transfer rights"],
    "event_of_default": ["event of default", "default"],
    "information_inspection_rights": ["information and inspection rights", "inspection rights"],
    "other_rights": ["other rights"],
    "non_compete_non_solicit": ["non-compete", "non-solicit", "non solicitation"],
    "rights_in_indian_subsidiary": ["rights in indian subsidiary"],
    "expenses": ["expenses", "costs", "fees"],
    "governing_law": ["governing law", "applicable law"],
    "dispute_resolution": ["dispute resolution", "arbitration", "jurisdiction"],
    "counterparts": ["counterparts"],
    "termination": ["termination"],
    # Legacy/backwards compatibility
    "parties": ["parties", "counterparties"],
    "covenants": ["covenants", "affirmative covenants", "negative covenants"],
    "board": ["board", "board of directors", "governance"],
    "observer": ["observer", "board observer"],
    "information_rights": ["information rights", "reporting", "financial information"],
    "audit_rights": ["audit rights", "inspection", "books and records"],
    "preemptive_pro_rata": ["pre-emptive", "preemptive", "pro rata", "right of first offer on new issuance"],
    "rofo": ["right of first offer", "rofo", "first offer"],
    "co_sale": ["co-sale", "tag along on secondary", "co sale"],
    "redemption": ["redemption", "buyback of shares"],
    "option_pool": ["option pool", "esop", "employee stock option"],
    "founder_vesting": ["vesting", "founder vesting", "cliff", "reverse vesting"],
    "founder_lockup": ["lock-in", "lockup", "non-compete", "non-solicit"],
    "transfer_restrictions": ["transfer restrictions", "permitted transfers", "secondary transfers"],
    "pay_to_play": ["pay-to-play", "pay to play"],
    "exclusivity": ["exclusivity", "no-shop", "no solicitation"],
    "break_fee": ["break fee", "termination fee", "expense reimbursement on termination"],
    "confidentiality": ["confidentiality", "non-disclosure", "nda"],
    "notices": ["notices", "notice"],
    "costs_expenses": ["costs", "expenses", "fees"],
    "timeline": ["timeline", "closing timeline", "completion schedule"],
    "exit": ["exit", "liquidity event", "qipo"],
}

_CANONICAL_HEADING_RAW_MAP = {
    "company": "company",
    "indian subsidiary": "indian_subsidiary",
    "founders": "founders",
    "investors": "new_investor",
    "new investor": "new_investor",
    "existing investors": "existing_investors",
    "investment amount": "investment_amount",
    "investors ownership": "new_investor_ownership",
    "subscription right": "subscription_right",
    "pre-money valuation": "pre_money_valuation",
    "valuation": "pre_money_valuation",
    "definitive documents": "definitive_documents",
    "capitalization": "capitalization",
    "shareholding pattern": "capitalization",
    "price per share": "price_per_share",
    "use of proceeds": "use_of_proceeds",
    "closing conditions": "closing_conditions",
    "representations & warranties; indemnification": "reps_warranties",
    "representations and warranties": "reps_warranties",
    "investor directors": "new_investor_director",
    "investor director": "new_investor_director",
    "shareholders meetings": "shareholders_meetings",
    "reserved matters": "reserved_matters",
    "protective provisions": "reserved_matters",
    "dividends": "dividend",
    "liquidation preference": "liquidation_preference",
    "conversion": "conversion",
    "voting rights": "voting_rights",
    "voting": "voting_rights",
    "anti-dilution": "anti_dilution",
    "registration rights": "registration_rights",
    "preemptive rights": "preemptive_rights",
    "pre-emptive rights": "preemptive_rights",
    "right of first refusal and co-sale": "right_of_first_refusal",
    "right of first refusal": "right_of_first_refusal",
    "tag along": "tag_along",
    "drag-along": "drag_along",
    "issuance or transfer to ant competitors": "new_investor_transfer_rights",
    "ant competitors": "non_compete_non_solicit",
    "transactions with ant competitors": "non_compete_non_solicit",
    "employment of founders and lock-up": "transfers_by_founders",
    "founder lock-up": "transfers_by_founders",
    "new investor's right to transfer": "new_investor_transfer_rights",
    "event of default": "event_of_default",
    "information and inspection rights": "information_inspection_rights",
    "other rights": "other_rights",
    "non-compete and non-solicit": "non_compete_non_solicit",
    "rights in indian subsidiary": "rights_in_indian_subsidiary",
    "expenses": "expenses",
    "governing law and dispute resolution": "dispute_resolution",
    "governing law": "governing_law",
    "dispute resolution": "dispute_resolution",
    "counterparts": "counterparts",
    "termination": "termination",
}


def _normalize_heading(text: str) -> str:
    if not text:
        return ""
    normalized = text.replace("\u2019", "'").replace("\u2018", "'")
    normalized = normalized.replace("\u201c", '"').replace("\u201d", '"')
    normalized = normalized.replace("：", ":")
    normalized = normalized.replace("&", " and ")
    normalized = normalized.strip().lower()
    normalized = normalized.rstrip(":")
    normalized = re.sub(r"[^a-z0-9\s'/-]", " ", normalized)
    normalized = " ".join(normalized.split())
    return normalized


CANONICAL_HEADING_MAP = {
    _normalize_heading(raw): key for raw, key in _CANONICAL_HEADING_RAW_MAP.items() if _normalize_heading(raw)
}

_HEAD_EXACT_LOOKUP: Dict[str, str] = {}
for _key, _keywords in HEAD_KEYWORDS.items():
    for _kw in _keywords:
        _norm = _normalize_heading(_kw)
        if _norm:
            _HEAD_EXACT_LOOKUP.setdefault(_norm, _key)


def _is_heading_candidate(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    normalized = _normalize_heading(raw)
    if not normalized:
        return False
    if normalized in CANONICAL_HEADING_MAP:
        return True
    if normalized in _HEAD_EXACT_LOOKUP:
        return True
    if raw.endswith(":") or raw.endswith("："):
        if len(normalized.split()) <= 12:
            return True
    if any(c.isalpha() for c in raw) and raw == raw.upper() and len(normalized.split()) <= 6:
        return True
    return False


_KEY_REMAP = {
    # Keep information_rights explicit for tests; audit_rights remains merged via BODY_HINTS below
    "audit_rights": "information_inspection_rights",
    "costs_expenses": "expenses",
    "preemptive_pro_rata": "preemptive_rights",
    "voting": "voting_rights",
}


def _extra_clause_keys(normalized_heading: str, primary_key: str | None, text: str) -> List[str]:
    extras: List[str] = []
    if normalized_heading == "right of first refusal and co-sale":
        extras.append("tag_along")
    if normalized_heading == "governing law and dispute resolution":
        extras.extend(["governing_law", "dispute_resolution"])
    if normalized_heading in {"employment of founders and lock-up", "founder lock-up"}:
        extras.append("non_compete_non_solicit")
    if normalized_heading in {"ant competitors", "transactions with ant competitors"}:
        extras.append("non_compete_non_solicit")
    if primary_key == "transfers_by_founders" and "non-compete" in text.lower():
        extras.append("non_compete_non_solicit")
    for key, patterns in SUPPLEMENTAL_HINTS.items():
        if key == primary_key:
            continue
        if any(pattern.search(text) for pattern in patterns):
            extras.append(key)
    dedup: List[str] = []
    for key in extras:
        canonical = _KEY_REMAP.get(key, key)
        if canonical == primary_key:
            continue
        if canonical not in dedup:
            dedup.append(canonical)
    return dedup

BODY_HINTS: Dict[str, List[re.Pattern[str]]] = {
    "registration_rights": [
        re.compile(r"\bregistration rights?\b", re.I),
    ],
    "event_of_default": [
        re.compile(r"\bevent of default\b", re.I),
    ],
    "exclusivity": [
        re.compile(r"\b(exclusive|exclusivity|no-?shop|no solicitation)\b", re.I),
        re.compile(r"\b(\d{1,3})\s*(?:day|days|business days)\b", re.I),
    ],
    "rofr": [
        re.compile(r"\bright of first refusal\b", re.I),
        re.compile(r"\bprior written consent\b", re.I),
    ],
    "rofo": [
        re.compile(r"\bright of first offer\b", re.I),
        re.compile(r"\bfirst offer\b", re.I),
    ],
    "co_sale": [
        re.compile(r"\bco-?sale\b|\btag[- ]along\b", re.I),
    ],
    "drag_along": [
        re.compile(r"\bdrag[- ]along\b", re.I),
        re.compile(r"\b(consenting|majority|supermajority)\s+shareholders", re.I),
    ],
    "tag_along": [
        re.compile(r"\btag[- ]along\b", re.I),
    ],
    "anti_dilution": [
        re.compile(r"\banti[- ]dilution\b|\bprice protection\b|\b(full ratchet|broad[- ]based|narrow[- ]based)\b", re.I),
    ],
    "liquidation_preference": [
        re.compile(r"\bliquidation preference\b", re.I),
        re.compile(r"\b(\d+(?:\.\d+)?)x\b", re.I),
        re.compile(r"\b(non[- ]participating|participating with cap|participating)\b", re.I),
    ],
    "dividend": [
        re.compile(r"\bdividend\b|\bcoupon\b", re.I),
        re.compile(r"\b(\d+(?:\.\d+)?)\s*%(\s*per\s*annum|p\.a\.)?\b", re.I),
    ],
    "redemption": [
        re.compile(r"\bredemption\b|\bput\b|\bbuyback\b", re.I),
        re.compile(r"\bafter\s+(\d+)\s*(?:years|yrs)\b", re.I),
    ],
    "preemptive_pro_rata": [
        re.compile(r"\bpre[- ]?emptive\b|\bpro rata\b|\bright to participate\b", re.I),
    ],
    "board": [
        re.compile(r"\bboard of directors\b|\bboard\b", re.I),
        re.compile(r"\b(\d+)\s+member", re.I),
        re.compile(r"\binvestor[- ]?director\b|\bnominee\b", re.I),
    ],
    "observer": [
        re.compile(r"\bobserver\b|\bboard observer\b", re.I),
    ],
    "information_rights": [
        re.compile(r"\b(?:monthly|quarterly|annual)\s+financial", re.I),
        re.compile(r"\bMIS\b|\bmanagement information\b", re.I),
    ],
    "audit_rights": [
        re.compile(r"\binspect(?:ion)?\b|\baudit\b|\bbooks and records\b", re.I),
    ],
    "option_pool": [
        re.compile(r"\b(option pool|esop)\b", re.I),
        re.compile(r"\b(\d+(?:\.\d+)?)\s*%\b", re.I),
    ],
    "founder_vesting": [
        re.compile(r"\bvesting\b|\breverse vesting\b|\bcliff\b", re.I),
        re.compile(r"\b(\d+)\s*year", re.I),
    ],
    "founder_lockup": [
        re.compile(r"\block[- ]?in\b|\blockup\b|\bnon[- ]compete\b|\bnon[- ]solicit\b", re.I),
    ],
    "transfer_restrictions": [
        re.compile(r"\btransfer\b|\bpermitted transf(?:er|ee)s\b|\bsecondary\b", re.I),
    ],
    "valuation": [
        re.compile(r"\b(pre|post)[- ]?money valuation\b", re.I),
        re.compile(r"\bUSD|INR|₹|\$\b", re.I),
    ],
    "price_per_share": [
        re.compile(r"\bprice per share\b|\bpps\b", re.I),
    ],
    "investment_amount": [
        re.compile(r"\baggregate (?:subscription|investment) amount\b|\bconsideration\b", re.I),
        re.compile(r"(USD|INR|₹|\$)\s?[\d,._]+", re.I),
    ],
    "securities": [
        re.compile(r"\b(preferred|equity|ccps|compulsorily|debenture)\b", re.I),
    ],
    "reserved_matters": [
        re.compile(r"\breserved matters\b|\bprotective provisions\b", re.I),
        re.compile(r"\bsupermajority\b|\b(\d{2,3})\s*%\b", re.I),
    ],
    "exclusivity_addl": [
        re.compile(r"\bno[- ]shop\b|\bno[- ]solicitation\b", re.I),
    ],
    "break_fee": [
        re.compile(r"\bbreak[- ]?fee\b|\btermination fee\b|\bexpense reimbursement\b", re.I),
    ],
    "confidentiality": [
        re.compile(r"\bconfidential\b|\bNDA\b|\bnon[- ]disclosure\b", re.I),
    ],
    "governing_law": [
        re.compile(r"\bgoverning law\b|\bshall be governed by\b", re.I),
    ],
    "dispute_resolution": [
        re.compile(r"\barbitration\b|\barbitral\b|\bjurisdiction\b|\bvenue\b", re.I),
    ],
    "notices": [
        re.compile(r"\bnotices\b|\bnotice\b|\bmode of service\b", re.I),
    ],
    "costs_expenses": [
        re.compile(r"\b(costs|expenses|fees)\b", re.I),
    ],
    "timeline": [
        re.compile(r"\bclosing (?:date|timeline|schedule)\b|\bcompletion\b", re.I),
    ],
    "exit": [
        re.compile(r"\bexit\b|\bliquidity event\b|\bqipo\b", re.I),
        re.compile(r"\b(\d{1,2})\s*(?:years|yrs)\b", re.I),
    ],
}

BODY_HINTS.setdefault("voting_rights", BODY_HINTS.get("voting", []))
BODY_HINTS.setdefault("preemptive_rights", BODY_HINTS.get("preemptive_pro_rata", []))
BODY_HINTS.setdefault("right_of_first_refusal", BODY_HINTS.get("rofr", []))
BODY_HINTS.setdefault("registration_rights", [])
BODY_HINTS.setdefault("information_inspection_rights", BODY_HINTS.get("information_rights", []) + BODY_HINTS.get("audit_rights", []))
BODY_HINTS.setdefault("expenses", BODY_HINTS.get("costs_expenses", []))

SUPPLEMENTAL_HINTS: Dict[str, List[re.Pattern[str]]] = {
    "definitive_documents": [re.compile(r"\bdefinitive document", re.I)],
}

_CURRENCY = r"(USD|INR|GBP|₹|£|\$)"
_AMOUNT = r"(?P<amount>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)"
_PERCENT = r"(?P<pct>\d{1,3}(?:\.\d+)?)\s*%"


def _to_float(raw: str | None) -> float | None:
    if not raw:
        return None
    return float(raw.replace(",", ""))


def extract_attributes(text: str) -> Dict[str, Any]:
    blob = text or ""
    attrs: Dict[str, Any] = {}

    # currency + amount with optional K/M suffix
    m_currency = re.search(rf"{_CURRENCY}\s*{_AMOUNT}\s*(?P<suf>[kKmM])?", blob, re.I)
    if m_currency:
        attrs["currency"] = m_currency.group(1)
        amt = _to_float(m_currency.group("amount"))
        suf = (m_currency.group("suf") or "").strip().lower()
        if suf == "k":
            amt = (amt or 0.0) * 1_000
        elif suf == "m":
            amt = (amt or 0.0) * 1_000_000
        attrs["amount"] = amt

    if "amount" not in attrs:
        m_amount = re.search(rf"\b{_AMOUNT}\s*(?P<suf2>[kKmM])?\b", blob)
        if m_amount:
            amt2 = _to_float(m_amount.group("amount"))
            suf2 = (m_amount.group("suf2") or "").strip().lower()
            if suf2 == "k":
                amt2 = (amt2 or 0.0) * 1_000
            elif suf2 == "m":
                amt2 = (amt2 or 0.0) * 1_000_000
            attrs["amount"] = amt2

    percents = list(re.finditer(_PERCENT, blob, re.I))
    if percents:
        attrs["percents"] = [float(match.group("pct")) for match in percents]
        attrs["percent"] = attrs["percents"][0]

    days = re.search(r"\b(?P<days>\d{1,3})\s*(?:business\s+)?days?\b", blob, re.I)
    if days:
        attrs["days"] = int(days.group("days"))

    months = re.search(r"\b(?P<months>\d{1,2})\s*months?\b", blob, re.I)
    if months:
        attrs["months"] = int(months.group("months"))

    years = re.search(r"\b(?P<years>\d{1,2})\s*(?:years|yrs)\b", blob, re.I)
    if years:
        attrs["years"] = int(years.group("years"))

    valuation = re.search(rf"\b(pre|post)[- ]?money valuation\b.*?{_CURRENCY}?\s*{_AMOUNT}", blob, re.I)
    if valuation:
        attrs["valuation_type"] = valuation.group(1).lower()
        attrs["valuation_currency"] = valuation.group(2)
        attrs["valuation_amount"] = _to_float(valuation.group("amount"))

    pps = re.search(rf"\bprice per share\b.*?{_CURRENCY}?\s*{_AMOUNT}", blob, re.I)
    if pps:
        attrs["pps_currency"] = pps.group(1)
        attrs["pps"] = _to_float(pps.group("amount"))

    pool = re.search(r"\b(option pool|esop)\b.*?(\d{1,2}(?:\.\d+)?)\s*%", blob, re.I)
    if pool:
        attrs["pool_percent"] = float(pool.group(2))

    board_size = re.search(r"\bboard\b.*?(\d+)\s+(?:member|director)s?", blob, re.I)
    if board_size:
        attrs["board_size"] = int(board_size.group(1))

    investor_directors = re.search(r"\binvestor[- ]?director\b.*?(\d+)", blob, re.I)
    if not investor_directors:
        investor_directors = re.search(r"(\d+)\s+investor[- ]?director", blob, re.I)
    if not investor_directors:
        investor_directors = re.search(r"(\d+)\s+investor[- ]?directors", blob, re.I)
    if investor_directors:
        attrs["investor_directors"] = int(investor_directors.group(1))

    # Drag threshold: allow percent either before or after the phrase
    drag_threshold = re.search(r"\bdrag[- ]along\b.*?(\d{1,3})\s*%", blob, re.I)
    if not drag_threshold and re.search(r"\bdrag[- ]along\b", blob, re.I):
        drag_threshold = re.search(r"(\d{1,3})\s*%.*?\bdrag[- ]along\b", blob, re.I)
    if drag_threshold:
        attrs["drag_threshold_percent"] = int(drag_threshold.group(1))

    tag_threshold = re.search(r"\btag[- ]along\b.*?(\d{1,3})\s*%", blob, re.I)
    if tag_threshold:
        attrs["tag_threshold_percent"] = int(tag_threshold.group(1))

    rofr_threshold = re.search(r"\bright of first refusal\b.*?(\d{1,3})\s*%", blob, re.I)
    if rofr_threshold:
        attrs["rofr_percent"] = int(rofr_threshold.group(1))

    liq_multiple = re.search(r"\b(\d+(?:\.\d+)?)x\b", blob, re.I)
    if liq_multiple:
        attrs["liq_multiple"] = float(liq_multiple.group(1))

    participation = re.search(r"\b(non[- ]participating|participating(?: with cap)?)\b", blob, re.I)
    if participation:
        attrs["participation"] = participation.group(1).lower()

    antidilution = re.search(r"\b(full ratchet|broad[- ]based|narrow[- ]based)\b", blob, re.I)
    if antidilution:
        attrs["antidilution_type"] = antidilution.group(1).lower()

    dividend_rate = re.search(r"\bdividend\b.*?(\d+(?:\.\d+)?)\s*%(?:\s*(?:per\s*annum|p\.a\.))?\b", blob, re.I)
    if dividend_rate:
        attrs["dividend_rate_percent"] = float(dividend_rate.group(1))

    redemption_after = re.search(r"\bredemption\b.*?\bafter\b.*?(\d+)\s*(?:years|yrs)\b", blob, re.I)
    if redemption_after:
        attrs["redemption_after_years"] = int(redemption_after.group(1))

    exclusivity_days = re.search(
        r"\b(exclusive|no-?shop|no solicitation)\b.*?(\d{1,3})\s*(?:business\s+)?days?\b",
        blob,
        re.I,
    )
    if exclusivity_days:
        attrs["exclusivity_days"] = int(exclusivity_days.group(2))

    break_fee = re.search(r"\bbreak[- ]?fee\b.*?" + rf"{_CURRENCY}\s*{_AMOUNT}", blob, re.I)
    if break_fee:
        attrs["break_currency"] = break_fee.group(1)
        attrs["break_fee"] = _to_float(break_fee.group("amount"))

    # Vesting years and cliff months (tolerate 'vest' or 'vesting', and order)
    vesting = re.search(r"\bvest(?:ing)?\b.*?(\d+)\s*year", blob, re.I)
    cliff = re.search(r"\bcliff\b.*?(\d+)\s*month", blob, re.I)
    if not cliff:
        cliff = re.search(r"(\d+)\s*month.*?\bcliff\b", blob, re.I)
    if vesting:
        attrs["vesting_years"] = int(vesting.group(1))
    if cliff:
        attrs["cliff_months"] = int(cliff.group(1))

    return attrs


def _classify_title(title: str) -> str | None:
    normalized = _normalize_heading(title)
    if not normalized:
        return None
    if normalized in CANONICAL_HEADING_MAP:
        return CANONICAL_HEADING_MAP[normalized]
    if normalized in _HEAD_EXACT_LOOKUP:
        return _HEAD_EXACT_LOOKUP[normalized]
    lowered = (title or "").strip().lower()
    for key, keywords in HEAD_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return key
    return None


def _classify_body(text: str) -> str | None:
    blob = text or ""
    for key, patterns in BODY_HINTS.items():
        if any(pattern.search(blob) for pattern in patterns):
            canonical = key if key in CLAUSE_KEYS else key.replace("_addl", "")
            return canonical
    return None


def _pick_clause_key(title: str, text: str) -> str | None:
    key = _classify_title(title)
    if not key:
        key = _classify_body(text)
    if key:
        return _KEY_REMAP.get(key, key)
    return None


def regex_extract_from_docling(pages_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocks = pages_json.get("blocks") or []
    snippets: List[Dict[str, Any]] = []
    emitted: set[tuple[str, str]] = set()

    # Phase 1: Strict table row mapping (prefer exact labels from left column)
    # Build per-row heading/value seen in parse_docling table flattening
    rows: Dict[int, Dict[str, Any]] = {}
    for b in blocks:
        meta = b.get("meta") or {}
        if "table_row" not in meta:
            continue
        row_idx = int(meta.get("table_row", -1))
        if row_idx < 0:
            continue
        col = meta.get("column")
        rows.setdefault(row_idx, {"heading": None, "value": None, "block_ids": []})
        rows[row_idx]["block_ids"].append(b.get("id"))
        if col == 0 and b.get("type") == "heading":
            rows[row_idx]["heading"] = b.get("text") or ""
        elif col == 1 and b.get("type") == "paragraph":
            rows[row_idx]["value"] = b.get("text") or ""

    for row_idx, data in sorted(rows.items()):
        heading_raw = (data.get("heading") or "").strip()
        value_text = (data.get("value") or "").strip()
        if not heading_raw or not value_text:
            continue
        norm_head = _normalize_heading(heading_raw)
        # Direct canonical lookup from heading maps
        keys: List[str] = []
        primary = CANONICAL_HEADING_MAP.get(norm_head) or _HEAD_EXACT_LOOKUP.get(norm_head)
        if primary:
            keys.append(_KEY_REMAP.get(primary, primary))
        # Augment with extras for composite headings
        keys.extend(_extra_clause_keys(norm_head, primary, value_text))
        # Deduplicate and emit
        for key in dict.fromkeys(keys):
            dedup_key = (key, value_text)
            if key and dedup_key not in emitted:
                emitted.add(dedup_key)
                snippets.append(
                    {
                        "clause_key": key,
                        "title": heading_raw.rstrip(":") or key.replace("_", " ").title(),
                        "text": value_text,
                        "block_ids": data.get("block_ids") or [],
                        "page_hint": None,
                        "attributes": extract_attributes(value_text),
                        "source": "docling_table",
                    }
                )

    # Phase 2: Sectionized headings/body for narrative parts
    sections = sectionize(blocks)
    for section in sections:
        title = section.get("title", "")
        body_text = section.get("text", "") or ""
        normalized_title = _normalize_heading(title)
        clause_key = _pick_clause_key(title, body_text)
        keys2: List[str] = []
        if clause_key:
            keys2.append(clause_key)
        keys2.extend(_extra_clause_keys(normalized_title, clause_key, body_text))
        if not keys2:
            continue
        attrs = extract_attributes(body_text)
        snippet_text = body_text
        snippet_title = title or None
        for key in dict.fromkeys(keys2):
            dedup_key = (key, snippet_text)
            if dedup_key in emitted:
                continue
            emitted.add(dedup_key)
            snippets.append(
                {
                    "clause_key": key,
                    "title": snippet_title or key.replace("_", " ").title(),
                    "text": snippet_text,
                    "block_ids": section.get("block_ids") or [],
                    "page_hint": section.get("page_start"),
                    "attributes": attrs,
                    "source": "docling",
                }
            )
    return snippets


def regex_extract_plaintext(text_plain: str) -> List[Dict[str, Any]]:
    blob = (text_plain or "").replace("\r\n", "\n").replace("\u3000", " ").replace("：", ":")
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", blob) if p.strip()]

    sections: List[Dict[str, Any]] = []
    preface: List[str] = []
    current_title: str | None = None
    current_body: List[str] = []

    def _flush_section() -> None:
        nonlocal current_title, current_body
        if current_title and current_body:
            sections.append({"title": current_title.strip(), "body": current_body[:]})
        current_body = []

    for para in paragraphs:
        if _is_heading_candidate(para):
            _flush_section()
            current_title = para.strip()
        else:
            if current_title:
                current_body.append(para.strip())
            else:
                preface.append(para.strip())

    _flush_section()

    results: List[Dict[str, Any]] = []
    emitted: set[tuple[str, str]] = set()
    for section in sections:
        title_raw = section["title"]
        body_parts = section["body"]
        body_text = "\n\n".join(body_parts).strip()
        if not body_text:
            continue
        normalized_title = _normalize_heading(title_raw)
        if normalized_title in {"term sheet", "investment terms"}:
            continue
        clause_key = _pick_clause_key(title_raw, body_text)
        keys: List[str] = []
        if clause_key:
            keys.append(clause_key)
        keys.extend(_extra_clause_keys(normalized_title, clause_key, body_text))
        if not keys:
            continue
        attrs = extract_attributes(body_text)
        snippet_title = title_raw.rstrip(":")
        snippet_text = f"{snippet_title}\n\n{body_text}".strip()
        for key in keys:
            key_text = (key, snippet_text)
            if key_text in emitted:
                continue
            emitted.add(key_text)
            results.append(
                {
                    "clause_key": key,
                    "title": snippet_title or key.replace("_", " ").title(),
                    "text": snippet_text,
                    "block_ids": [],
                    "page_hint": None,
                    "attributes": attrs,
                    "source": "plaintext",
                }
            )

    if not results and preface:
        preface_text = "\n\n".join(preface).strip()
        if preface_text:
            results.append(
                {
                    "clause_key": "document_overview",
                    "title": "Document Overview",
                    "text": preface_text[:500] + ("..." if len(preface_text) > 500 else ""),
                    "block_ids": [],
                    "page_hint": None,
                    "attributes": {},
                    "source": "plaintext",
                }
            )

    return results

