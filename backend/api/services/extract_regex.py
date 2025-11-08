from __future__ import annotations

import re
from typing import Dict, List


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


