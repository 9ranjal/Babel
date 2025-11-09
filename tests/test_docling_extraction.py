from backend.api.services.extract_llm import normalize_snippets
from backend.api.services.extract_regex import regex_extract_from_docling


def test_docling_section_extraction_captures_attributes():
    blocks = [
        {"id": "h1", "type": "heading", "page": 0, "text": "Section 1. Exclusivity"},
        {"id": "p1", "type": "para", "page": 0, "text": "The Company agrees to an exclusive no-shop period of 45 business days."},
        {"id": "h2", "type": "heading", "page": 0, "text": "Section 2. Right of First Refusal (ROFR)"},
        {"id": "p2", "type": "para", "page": 0, "text": "Investors hold a right of first refusal over any founder transfer above 60%."},
        {"id": "h3", "type": "heading", "page": 0, "text": "Section 3. Co-Sale Rights"},
        {"id": "p3", "type": "para", "page": 0, "text": "Investors may exercise co-sale (tag-along) rights for any founder sale exceeding 15%."},
        {"id": "h4", "type": "heading", "page": 0, "text": "Section 4. Drag-Along"},
        {"id": "p4", "type": "para", "page": 0, "text": "A supermajority of 60% may drag along all shareholders with a 2.0x floor."},
        {"id": "h5", "type": "heading", "page": 0, "text": "Section 5. Liquidation Preference"},
        {"id": "p5", "type": "para", "page": 0, "text": "Series A enjoys a participating liquidation preference of 2.0x non-participating floor."},
        {"id": "h6", "type": "heading", "page": 0, "text": "Section 6. Anti-Dilution"},
        {"id": "p6", "type": "para", "page": 0, "text": "Anti-dilution adjustments shall be broad-based weighted average."},
        {"id": "h7", "type": "heading", "page": 1, "text": "Section 7. Board Composition"},
        {"id": "p7", "type": "para", "page": 1, "text": "The board will consist of 5 directors, including 2 investor directors."},
        {"id": "h8", "type": "heading", "page": 1, "text": "Section 8. Board Observer"},
        {"id": "p8", "type": "para", "page": 1, "text": "Lead Investor may appoint one non-voting board observer."},
        {"id": "h9", "type": "heading", "page": 1, "text": "Section 9. Information Rights"},
        {"id": "p9", "type": "para", "page": 1, "text": "Company shall deliver monthly MIS and quarterly financial statements."},
        {"id": "h10", "type": "heading", "page": 1, "text": "Section 10. Option Pool"},
        {"id": "p10", "type": "para", "page": 1, "text": "Option pool to be increased to 12% on a post-money basis."},
        {"id": "h11", "type": "heading", "page": 1, "text": "Section 11. Founder Vesting"},
        {"id": "p11", "type": "para", "page": 1, "text": "Founders vest over 4 years with a 12 month cliff under reverse vesting."},
    ]
    snippets = regex_extract_from_docling({"blocks": blocks})
    snippet_map = {snippet["clause_key"]: snippet for snippet in snippets}

    expected_keys = {
        "exclusivity",
        "rofr",
        "co_sale",
        "drag_along",
        "liquidation_preference",
        "anti_dilution",
        "board",
        "observer",
        "information_rights",
        "option_pool",
        "founder_vesting",
    }
    assert expected_keys.issubset(snippet_map.keys())

    assert snippet_map["exclusivity"]["attributes"]["exclusivity_days"] == 45
    assert snippet_map["rofr"]["attributes"]["rofr_percent"] == 60
    assert snippet_map["co_sale"]["attributes"]["tag_threshold_percent"] == 15
    assert snippet_map["drag_along"]["attributes"]["drag_threshold_percent"] == 60
    assert snippet_map["liquidation_preference"]["attributes"]["liq_multiple"] == 2.0
    assert snippet_map["liquidation_preference"]["attributes"]["participation"] == "participating"
    assert snippet_map["anti_dilution"]["attributes"]["antidilution_type"] == "broad-based"
    assert snippet_map["board"]["attributes"]["board_size"] == 5
    assert snippet_map["board"]["attributes"]["investor_directors"] == 2
    assert snippet_map["option_pool"]["attributes"]["pool_percent"] == 12.0
    assert snippet_map["founder_vesting"]["attributes"]["vesting_years"] == 4
    assert snippet_map["founder_vesting"]["attributes"]["cliff_months"] == 12

    normalized = normalize_snippets(snippets, temperature=0.0)
    norm_map = {item["clause_key"]: item for item in normalized}

    assert norm_map["exclusivity"]["page_hint"] == 0
    assert norm_map["option_pool"]["page_hint"] == 1
    for key in expected_keys:
        block_ids = norm_map[key]["json_meta"].get("block_ids")
        assert block_ids, f"{key} missing block_ids metadata"

    attr_expected = {
        "exclusivity",
        "rofr",
        "co_sale",
        "drag_along",
        "liquidation_preference",
        "anti_dilution",
        "board",
        "option_pool",
        "founder_vesting",
    }
    for key in attr_expected:
        assert norm_map[key]["attributes"], f"{key} missing attributes payload"

