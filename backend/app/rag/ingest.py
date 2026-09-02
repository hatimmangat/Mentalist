"""
Run this once (and any time the corpus changes) to build the vector index:

    python -m app.rag.ingest
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.rag.chunker import chunk_corpus_directory
from app.rag.vectorstore import get_vector_store

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "corpus")


def main():
    print(f"[ingest] chunking corpus at {CORPUS_DIR}")
    chunks = chunk_corpus_directory(CORPUS_DIR)
    print(f"[ingest] produced {len(chunks)} chunks from corpus")

    store = get_vector_store()
    if store.is_populated():
        print("[ingest] existing collection found, clearing before re-ingest")
        store.clear()

    print("[ingest] embedding + storing chunks (loads the local embedding model on first run, may take a minute)")
    store.add_chunks(chunks)
    print(f"[ingest] done. collection now has {store.collection.count()} vectors")


if __name__ == "__main__":
    main()
