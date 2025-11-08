from __future__ import annotations

from typing import Dict, List


def build_graph(document_id: str, clauses: List[Dict]) -> Dict:
    nodes: List[Dict] = [
        {"data": {"id": f"doc:{document_id}", "type": "document", "label": "Term Sheet"}}
    ]
    edges: List[Dict] = []
    for c in clauses:
        cid = c["id"] if "id" in c else c.get("clause_id") or c.get("start_idx", 0)
        nid = f"clause:{cid}"
        label = c.get("title") or c.get("clause_key") or "Clause"
        nodes.append({"data": {"id": nid, "type": "clause", "label": label}})
        edges.append({"data": {"id": f"e:{document_id}:{cid}", "source": f"doc:{document_id}", "target": nid}})
    return {"nodes": nodes, "edges": edges}


