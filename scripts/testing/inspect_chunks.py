from __future__ import annotations

import difflib
import json
import os
from collections import Counter
from typing import Any, Dict, List, Tuple

from backend.api.services.parse_pdf import parse_pdf_bytes
from backend.api.services.parse_docx import parse_docx_bytes
from backend.api.services.extract_regex import regex_extract_plaintext
from backend.api.services.extract_llm import normalize_snippets


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def load_bands(repo_root: str) -> Dict[str, Any]:
    with open(os.path.join(repo_root, "packages", "batna", "seed", "bands.json"), "r") as f:
        return json.load(f)


def analyze_file(path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    data = read_bytes(path)
    parsed = parse_pdf_bytes(data) if ext == ".pdf" else parse_docx_bytes(data)
    text_plain = parsed.get("text_plain") or ""
    snippets = regex_extract_plaintext(text_plain)
    normalized = normalize_snippets(snippets, temperature=0.0)
    return normalized, {"file": name, "ext": ext}


def summarize_securities(snippets: List[Dict[str, Any]]) -> Dict[str, Any]:
    secs = [s for s in snippets if s.get("clause_key") == "securities"]
    dup_pairs: List[Tuple[int, int, float]] = []
    for i in range(1, len(secs)):
        a = (secs[i - 1].get("text") or "").strip()
        b = (secs[i].get("text") or "").strip()
        r = difflib.SequenceMatcher(None, a, b).ratio()
        if r >= 0.9:
            dup_pairs.append((i - 1, i, r))
    samples = []
    for i, s in enumerate(secs):
        text = (s.get("text") or "").strip()
        preview = text.splitlines()[0][:120]
        samples.append(
            {
                "idx": i,
                "page_hint": s.get("page_hint"),
                "chars": len(text),
                "words": len(text.split()),
                "preview": preview,
            }
        )
    return {"count": len(secs), "samples": samples, "potential_duplicate_pairs": dup_pairs}


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=. python scripts/testing/inspect_chunks.py <file_or_dir>")
        sys.exit(2)

    base = sys.argv[1]
    targets: List[str] = []
    if os.path.isdir(base):
        for fn in os.listdir(base):
            if fn.lower().endswith((".pdf", ".docx")):
                targets.append(os.path.join(base, fn))
    else:
        targets.append(base)

    repo_root = os.getcwd()
    bands = load_bands(repo_root)
    band_keys = {c["clause_key"] for c in bands.get("clauses", [])}

    for path in sorted(targets):
        snippets, meta = analyze_file(path)
        counts = Counter(s.get("clause_key") for s in snippets)
        covered = sum(v for k, v in counts.items() if k in band_keys)
        sec_summary = summarize_securities(snippets)
        print(f"\n=== {meta['file']} ===")
        print(f"total_snippets={len(snippets)} unique_keys={len(counts)} band_covered_snippets={covered}")
        print("top_keys:", ", ".join(f"{k}:{v}" for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]))
        print(f"securities_count={sec_summary['count']}")
        for s in sec_summary["samples"]:
            print(
                f"  [idx={s['idx']}] page={s['page_hint']} chars={s['chars']} words={s['words']} preview={s['preview']!r}"
            )
        for i, j, r in sec_summary["potential_duplicate_pairs"]:
            print(f"  -> potential_duplicate pair ({i},{j}) similarity={r:.2f}")


if __name__ == "__main__":
    main()


