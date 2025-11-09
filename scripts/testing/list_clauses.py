from __future__ import annotations

from collections import Counter
import os
import sys

from backend.api.services.parse_pdf import parse_pdf_bytes
from backend.api.services.parse_docx import parse_docx_bytes
from backend.api.services.extract_regex import regex_extract_plaintext


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=. python scripts/testing/list_clauses.py <file_or_dir> [more_paths...]")
        sys.exit(2)
    inputs = []
    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            for fn in os.listdir(arg):
                if fn.lower().endswith((".pdf", ".docx")):
                    inputs.append(os.path.join(arg, fn))
        else:
            inputs.append(arg)

    for path in sorted(inputs):
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()
        data = read_bytes(path)
        if ext == ".pdf":
            parsed = parse_pdf_bytes(data)
        else:
            parsed = parse_docx_bytes(data)
        text_plain = parsed.get("text_plain") or ""
        snippets = regex_extract_plaintext(text_plain)
        counts = Counter(s.get("clause_key") for s in snippets)
        print(f"\n=== {name} ===")
        for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()


