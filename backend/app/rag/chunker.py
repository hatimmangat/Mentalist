"""
Document chunking for the RAG pipeline.

Strategy: markdown-aware chunking. Each source document is split first by
'## ' headers (semantic sections written by a human), then any section that
is still too long is further split by sentence boundaries with overlap, so
we never cut a sentence in half and we preserve topical coherence per chunk.
"""
import re
import os
from dataclasses import dataclass, field
from typing import List

CHUNK_MAX_CHARS = 900
CHUNK_OVERLAP_CHARS = 150


@dataclass
class Chunk:
    text: str
    source_file: str
    doc_title: str
    section_title: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


def _split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z(])', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _pack_sentences(sentences: List[str], max_chars: int, overlap_chars: int) -> List[str]:
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            overlap = current[-overlap_chars:] if current else ""
            current = f"{overlap} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def chunk_markdown_file(path: str) -> List[Chunk]:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    filename = os.path.basename(path)

    title_match = re.match(r"^#\s+(.+)", raw.strip())
    doc_title = title_match.group(1).strip() if title_match else filename

    sections = re.split(r"\n(?=## )", raw)
    chunks: List[Chunk] = []
    chunk_idx = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue
        header_match = re.match(r"^##\s+(.+)", section)
        if header_match:
            section_title = header_match.group(1).strip()
            body = section[header_match.end():].strip()
        else:
            section_title = "Overview"
            body = re.sub(r"^#\s+.+\n?", "", section).strip()

        if not body:
            continue

        if len(body) <= CHUNK_MAX_CHARS:
            pieces = [body]
        else:
            sentences = _split_into_sentences(body)
            pieces = _pack_sentences(sentences, CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS)

        for piece in pieces:
            contextualized = f"{doc_title} — {section_title}: {piece}"
            chunks.append(Chunk(
                text=contextualized,
                source_file=filename,
                doc_title=doc_title,
                section_title=section_title,
                chunk_index=chunk_idx,
            ))
            chunk_idx += 1

    return chunks


def chunk_corpus_directory(corpus_dir: str) -> List[Chunk]:
    all_chunks: List[Chunk] = []
    for filename in sorted(os.listdir(corpus_dir)):
        if filename.endswith(".md"):
            path = os.path.join(corpus_dir, filename)
            all_chunks.extend(chunk_markdown_file(path))
    return all_chunks
