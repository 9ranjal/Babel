import re
from typing import Optional, Tuple

_ROMAN = r"(?:M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))"
_NUM_PAT = re.compile(
    rf"^\s*(?:Section\s+\d+(?:\.\d+)*|{_ROMAN}|[A-Z]\.|[a-z]\)|\d+(?:\.\d+)*|\(\d+\)|\([a-z]\)|\({_ROMAN}\))[\s\.:–-]*",
    re.IGNORECASE,
)


def strip_leading_numbering(s: Optional[str]) -> Tuple[str, Optional[str]]:
    text = s or ""
    match = _NUM_PAT.match(text)
    if not match:
        return text, None
    stripped = text[match.end() :].lstrip()
    return stripped, match.group(0).strip()


