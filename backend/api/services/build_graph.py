from __future__ import annotations

from typing import Dict, List
from .band_map import DEFAULT_LEVERAGE
from .banding import band_clause

# Top-level category mapping inspired by user spec
CATEGORY_TO_KEYS: Dict[str, List[str]] = {
    "Economics": [
        "liquidation_preference",
        "dividend",
        "price_per_share",
        "pre_money_valuation",
        "investment_amount",
        "redemption",
        "pay_to_play",
    ],
    "Ownership & Dilution": [
        "anti_dilution",
        "preemptive_pro_rata",
        "preemptive_pro_rata",
        "option_pool",
        "securities",
    ],
    "Control & Governance": [
        "board",
        "observer",
        "voting_rights",
        "voting",
        "reserved_matters",
    ],
    "Transfer & Liquidity": [
        "rofr",
        "rofo",
        "rofr",
        "co_sale",
        "tag_along",
        "drag_along",
        "transfer_restrictions",
        "transfers_by_founders",
    ],
    "Information & Oversight": [
        "information_rights",
        "audit_rights",
        "registration_rights",
    ],
    "Founder/Team Matters": [
        "founder_vesting",
        "founder_lockup",
        "non_compete_non_solicit",
        "option_pool",
    ],
    "Deal Process & Closing": [
        "closing_conditions",
        "timeline",
        "use_of_proceeds",
        "exclusivity",
        "break_fee",
        "definitive_documents",
        "counterparts",
        "termination",
    ],
    "Legal Boilerplate": [
        "reps_warranties",
        "confidentiality",
        "governing_law",
        "dispute_resolution",
        "notices",
        "expenses",
        "expenses",
    ],
    "Company/Structure": [
        "company",
        "indian_subsidiary",
        "rights_in_indian_subsidiary",
        "existing_investors",
        "existing_shareholder_rights",
        "capitalization",
        "conversion",
        "shareholder_meetings",
        "event_of_default",
        "new_investor",
        "ownership_post",
    ],
}

# Reverse lookup from clause key to category
KEY_TO_CATEGORY: Dict[str, str] = {
    key: category for category, keys in CATEGORY_TO_KEYS.items() for key in keys
}

# Aliases / normalization map
ALIASES: Dict[str, str] = {
    "information_inspection_rights": "information_rights",
    "right_of_first_refusal": "rofr",
    "preemptive_rights": "preemptive_pro_rata",
    "shareholders_meetings": "shareholder_meetings",
    "new_investor_transfer_rights": "transfer_restrictions",
    "new_investor_ownership": "ownership_post",
}


def canonical(key: str | None) -> str:
    raw = (key or "").strip()
    return ALIASES.get(raw, raw)

FRIENDLY_LABELS: Dict[str, str] = {
    "liquidation_preference": "Liquidation Preference",
    "dividend": "Dividends",
    "price_per_share": "Price per Share",
    "pre_money_valuation": "Valuation",
    "investment_amount": "Investment Amount",
    "anti_dilution": "Anti‑Dilution",
    "preemptive_pro_rata": "Pre‑emptive Rights",
    "option_pool": "Option Pool",
    "securities": "Securities",
    "reserved_matters": "Reserved Matters",
    "voting_rights": "Voting",
    "board": "Board",
    "rofr": "ROFR",
    "rofo": "ROFO",
    "tag_along": "Tag‑Along",
    "drag_along": "Drag‑Along",
    "transfer_restrictions": "Transfer Restrictions",
    "information_rights": "Information Rights",
    "registration_rights": "Registration Rights",
    "founder_vesting": "Founder Vesting",
    "non_compete_non_solicit": "Non‑compete / Non‑solicit",
    "closing_conditions": "Closing Conditions",
    "exclusivity": "Exclusivity",
    "use_of_proceeds": "Use of Proceeds",
    "definitive_documents": "Definitive Documents",
    "counterparts": "Counterparts",
    "termination": "Termination",
    "confidentiality": "Confidentiality",
    "dispute_resolution": "Dispute Resolution",
    "governing_law": "Governing Law",
    "reps_warranties": "Reps & Warranties",
    "expenses": "Expenses",
    "company": "Company",
    "indian_subsidiary": "Indian Subsidiary",
    "rights_in_indian_subsidiary": "Rights in Indian Subsidiary",
    "existing_investors": "Existing Investors",
    "existing_shareholder_rights": "Existing Shareholder Rights",
    "capitalization": "Shareholding Pattern",
    "conversion": "Conversion",
    "shareholder_meetings": "Shareholder Meetings",
    "event_of_default": "Event of Default",
    "new_investor": "New Investor",
    "ownership_post": "Investors' Ownership",
}

def display_label(key: str, title: str | None) -> str:
    # Prefer short friendly label; fall back to trimmed title if key unknown
    if key in FRIENDLY_LABELS:
        return FRIENDLY_LABELS[key]
    t = (title or "").strip()
    if len(t) > 60 or t.count(" ") > 8:
        return key.replace("_", " ").title()
    return t or key.replace("_", " ").title()

def _slug(text: str) -> str:
    return (
        (text or "")
        .strip()
        .lower()
        .replace("&", "and")
        .replace("/", " ")
        .replace("  ", " ")
        .replace(" ", "_")
    )


def build_graph(document_id: str, clauses: List[Dict]) -> Dict:
    nodes: List[Dict] = [
        {"data": {"id": f"doc:{document_id}", "type": "document", "label": "Term Sheet"}}
    ]
    edges: List[Dict] = []

    # Track which categories are present and which clauses belong to them
    present_categories: Dict[str, Dict[str, str]] = {}  # cat_label -> {id, slug}
    cat_to_clause_ids: Dict[str, List[str]] = {}
    key_to_clause_ids: Dict[str, List[str]] = {}
    clause_key_to_node_id: Dict[str, str] = {}
    clause_key_to_source_clause_ids: Dict[str, List[str]] = {}

    # Create clause nodes and bucket them
    for c in clauses or []:
        cid = c.get("id") or c.get("clause_id") or c.get("start_idx", 0)
        nid = f"clause:{cid}"
        raw_title = c.get("title")
        key = canonical(c.get("clause_key"))
        category = KEY_TO_CATEGORY.get(key)

        # For demo cleanliness: skip unbucketed keys entirely
        if not category:
            continue

        # Compute banding metadata from attributes if available
        band_info = band_clause(key, c.get("attributes") or {}, DEFAULT_LEVERAGE)

        # Collapse duplicates: one node per canonical clause key
        if key in clause_key_to_node_id:
            # Track additional source clause ids for potential future use
            clause_key_to_source_clause_ids.setdefault(key, []).append(str(cid))
        else:
            friendly = display_label(key, raw_title)
            node_id = f"clkey:{key}"
            nodes.append(
                {
                    "data": {
                        "id": node_id,
                        "type": "clause",
                        "label": friendly,
                        "key": key,
                        "bucket": category,
                        "band": (band_info.get("band") or {}).get("name"),
                        "badge": band_info.get("badge"),
                        "tilt": band_info.get("tilt"),
                        "clauseId": str(cid),  # primary representative id for click-through
                    }
                }
            )
            clause_key_to_node_id[key] = node_id
            clause_key_to_source_clause_ids.setdefault(key, []).append(str(cid))

        # Track membership for second-order edges (dedup ids)
        ids = key_to_clause_ids.setdefault(key, [])
        node_id = clause_key_to_node_id[key]
        if node_id not in ids:
            ids.append(node_id)

        # Only include categories that actually appear (hide empty)
        if category:
            slug = _slug(category)
            cat_id = f"cat:{slug}"
            present_categories.setdefault(category, {"id": cat_id, "slug": slug})
            lst = cat_to_clause_ids.setdefault(category, [])
            if node_id not in lst:
                lst.append(node_id)

    # Emit category nodes and hierarchical edges (doc→category, category→clause)
    for cat_label, meta in present_categories.items():
        cat_id = meta["id"]
        size_score = len(cat_to_clause_ids.get(cat_label, [])) or 1
        nodes.append(
            {
                "data": {
                    "id": cat_id,
                    "type": "category",
                    "label": cat_label,
                    "bucket": cat_label,
                    "sizeScore": size_score,
                }
            }
        )
        # doc → category edge
        edges.append(
            {
                "data": {
                    "id": f"e:{document_id}:{meta['slug']}",
                    "source": f"doc:{document_id}",
                    "target": cat_id,
                    "edgeType": "doc-cat",
                    "weight": size_score,
                    "bucket": cat_label,
                }
            }
        )
        # category → clause edges
        for clause_nid in cat_to_clause_ids.get(cat_label, []):
            edges.append(
                {
                    "data": {
                        "id": f"e:{meta['slug']}:{clause_nid}",
                        "source": cat_id,
                        "target": clause_nid,
                        "edgeType": "cat-clause",
                        "bucket": cat_label,
                    }
                }
            )

    # Add second-order clause↔clause edges where both endpoints exist
    SECOND_ORDER_LINKS: Dict[str, List[str]] = {
        "rofr": ["tag_along", "rofo"],
        "tag_along": ["rofr", "drag_along"],
        "drag_along": ["exit"],
        "exclusivity": ["rofo", "rofr", "tag_along"],
        "anti_dilution": ["pay_to_play"],
        "liquidation_preference": ["reserved_matters", "board"],
    }
    added_secondary: set[tuple[str, str]] = set()
    for src_key, targets in SECOND_ORDER_LINKS.items():
        for dst_key in targets:
            for src_nid in key_to_clause_ids.get(src_key, []):
                for dst_nid in key_to_clause_ids.get(dst_key, []):
                    if src_nid == dst_nid:
                        continue
                    pair = (src_nid, dst_nid)
                    if pair in added_secondary:
                        continue
                    added_secondary.add(pair)
                    edges.append(
                        {
                            "data": {
                                "id": f"s:{src_nid}:{dst_nid}",
                                "source": src_nid,
                                "target": dst_nid,
                                "edgeType": "secondary",
                            }
                        }
                    )

    return {"nodes": nodes, "edges": edges}


