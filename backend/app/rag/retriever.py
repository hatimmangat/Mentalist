from typing import List, Dict
from app.rag.vectorstore import get_vector_store

SIMILARITY_FLOOR = 0.15


def retrieve(query: str, top_k: int = 4) -> List[Dict]:
    store = get_vector_store()
    hits = store.query(query, top_k=top_k)
    return [h for h in hits if h["similarity"] >= SIMILARITY_FLOOR]


def format_context_block(hits: List[Dict]) -> str:
    if not hits:
        return ""
    lines = ["Relevant reference material retrieved for this query:\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(
            f"[{i}] From \"{hit['doc_title']}\" ({hit['section_title']}):\n{hit['text']}\n"
        )
    return "\n".join(lines)


def retrieve_and_format(query: str, top_k: int = 4) -> Dict:
    hits = retrieve(query, top_k=top_k)
    return {
        "context_block": format_context_block(hits),
        "sources": [
            {"doc_title": h["doc_title"], "section_title": h["section_title"], "similarity": round(h["similarity"], 3)}
            for h in hits
        ],
    }
