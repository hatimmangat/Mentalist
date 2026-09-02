import os
import chromadb
from typing import List
from app.rag.chunker import Chunk
from app.rag.embeddings import embed_texts, embed_query

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_store")
COLLECTION_NAME = "mentalist_corpus"


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def is_populated(self) -> bool:
        return self.collection.count() > 0

    def clear(self):
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[Chunk], batch_size: int = 64):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.text for c in batch]
            embeddings = embed_texts(texts)
            ids = [f"{c.source_file}::{c.chunk_index}" for c in batch]
            metadatas = [{
                "source_file": c.source_file,
                "doc_title": c.doc_title,
                "section_title": c.section_title,
                "chunk_index": c.chunk_index,
            } for c in batch]
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

    def query(self, query_text: str, top_k: int = 4):
        query_embedding = embed_query(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        hits = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                hits.append({
                    "text": doc,
                    "source_file": meta.get("source_file"),
                    "doc_title": meta.get("doc_title"),
                    "section_title": meta.get("section_title"),
                    "similarity": 1 - dist,
                })
        return hits


_store_singleton = None


def get_vector_store() -> VectorStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = VectorStore()
    return _store_singleton
