from __future__ import annotations

import re
from typing import Any, Dict, List

from .numbering import strip_leading_numbering
from .sectionizer import sectionize


CLAUSE_KEYS = [
    "parties",
    "investment_amount",
    "valuation",
    "price_per_share",
    "securities",
    "use_of_proceeds",
    "closing_conditions",
    "reps_warranties",
    "covenants",
    "board",
    "observer",
    "voting",
    "reserved_matters",
    "information_rights",
    "audit_rights",
    "anti_dilution",
    "preemptive_pro_rata",
    "rofo",
    "rofr",
    "co_sale",
    "drag_along",
    "tag_along",
    "liquidation_preference",
    "dividend",
    "redemption",
    "option_pool",
    "founder_vesting",
    "founder_lockup",
    "transfer_restrictions",
    "pay_to_play",
    "exclusivity",
    "break_fee",
    "confidentiality",
    "governing_law",
    "dispute_resolution",
    "notices",
    "costs_expenses",
    "timeline",
    "exit",
]

HEAD_KEYWORDS: Dict[str, List[str]] = {
    "parties": ["parties", "counterparties"],
    "investment_amount": [
        "investment amount",
        "subscription amount",
        "aggregate consideration",
        "amount invested",
    ],
    "valuation": ["valuation", "pre-money", "post-money"],
    "price_per_share": ["price per share", "pps", "subscription price"],
    "securities": ["securities", "class of securities", "instrument", "security"],
    "use_of_proceeds": ["use of proceeds", "application of funds"],
    "closing_conditions": ["conditions precedent", "conditions to closing", "closing conditions"],
    "reps_warranties": ["representations", "warranties", "reps and warranties"],
    "covenants": ["covenants", "affirmative covenants", "negative covenants"],
    "observer": ["observer", "board observer"],
    "board": ["board", "board of directors", "governance"],
    "voting": ["voting", "shareholder voting", "consents"],
    "reserved_matters": [
        "reserved matters",
        "protective provisions",
        "affirmative vote matters",
        "matters requiring consent",
    ],
    "information_rights": ["information rights", "reporting", "financial information"],
    "audit_rights": ["audit rights", "inspection", "books and records"],
    "anti_dilution": ["anti-dilution", "price protection", "down round protection"],
    "preemptive_pro_rata": ["pre-emptive", "preemptive", "pro rata", "right of first offer on new issuance"],
    "rofo": ["right of first offer", "rofo", "first offer"],
    "rofr": ["right of first refusal", "rofr", "purchase option on transfer"],
    "co_sale": ["co-sale", "tag along on secondary", "co sale"],
    "drag_along": ["drag-along", "drag along"],
    "tag_along": ["tag-along", "tag along"],
    "liquidation_preference": ["liquidation preference", "preference on sale", "distribution waterfall"],
    "dividend": ["dividend", "coupon"],
    "redemption": ["redemption", "buyback of shares"],
    "option_pool": ["option pool", "esop", "employee stock option"],
    "founder_vesting": ["vesting", "founder vesting", "cliff", "reverse vesting"],
    "founder_lockup": ["lock-in", "lockup", "non-compete", "non-solicit"],
    "transfer_restrictions": ["transfer restrictions", "permitted transfers", "secondary transfers"],
    "pay_to_play": ["pay-to-play", "pay to play"],
    "exclusivity": ["exclusivity", "no-shop", "no solicitation"],
    "break_fee": ["break fee", "termination fee", "expense reimbursement on termination"],
    "confidentiality": ["confidentiality", "non-disclosure", "nda"],
    "governing_law": ["governing law", "applicable law"],
    "dispute_resolution": ["dispute resolution", "arbitration", "jurisdiction"],
    "notices": ["notices", "notice"],
    "costs_expenses": ["costs", "expenses", "fees"],
    "timeline": ["timeline", "closing timeline", "completion schedule"],
    "exit": ["exit", "liquidity event", "qipo"],
}

BODY_HINTS: Dict[str, List[re.Pattern[str]]] = {
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
    normalized = (title or "").strip().lower()
    if not normalized:
        return None
    for key, keywords in HEAD_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
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
    if key:
        return key
    return _classify_body(text)


def regex_extract_from_docling(pages_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocks = pages_json.get("blocks") or []
    sections = sectionize(blocks)
    snippets: List[Dict[str, Any]] = []
    for section in sections:
        clause_key = _pick_clause_key(section.get("title", ""), section.get("text", ""))
        if not clause_key:
            continue
        attrs = extract_attributes(section.get("text", ""))
        snippets.append(
            {
                "clause_key": clause_key,
                "title": section.get("title") or clause_key.replace("_", " ").title(),
                "text": section.get("text") or "",
                "block_ids": section.get("block_ids") or [],
                "page_hint": section.get("page_start"),
                "attributes": attrs,
                "source": "docling",
            }
        )
    return snippets


def regex_extract_plaintext(text_plain: str) -> List[Dict[str, Any]]:
    chunks = re.split(r"\n{2,}", text_plain or "")
    results: List[Dict[str, Any]] = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        first_line = chunk.split("\n", 1)[0]
        title, _ = strip_leading_numbering(first_line)
        clause_key = _pick_clause_key(title, chunk)
        if not clause_key:
            continue
        # Minimal-length filter: drop label-only micro-snippets unless attributes are present
        blob = chunk.strip()
        word_count = len(blob.split())
        char_count = len(blob)
        attrs = extract_attributes(chunk)
        if (word_count < 3 or char_count < 20) and not attrs:
            continue
        results.append(
            {
                "clause_key": clause_key,
                "title": title or clause_key.replace("_", " ").title(),
                "text": chunk,
                "block_ids": [],
                "page_hint": None,
                "attributes": attrs,
                "source": "plaintext",
            }
        )
    return results

