"""
Embedding generation for the RAG pipeline. Uses sentence-transformers
running locally (all-MiniLM-L6-v2), NOT an API — zero marginal cost, no
external rate limit, works even if the LLM provider has an outage.
"""
from functools import lru_cache
from typing import List
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedder()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    return embed_texts([query])[0]
