"""
Chunking strategies for the Support Knowledge Copilot.

Two strategies:
1. heading_chunk  -> splits Markdown by ## headings
2. fixed_chunk    -> fixed-size word windows with overlap

Every chunk gets a stable chunk_id and carries metadata so the
dense (Qdrant) and sparse (BM25) indexes point to the same record.
"""

import re
import hashlib
from dataclasses import dataclass,field
from typing import List,Dict

@dataclass
class Chunk:
    chunk_id:str
    text:str
    source:str
    section:str
    strategy:str
    metadata:Dict = field(default_factory=dict)


def _make_chunk_id(source:str, section:str, strategy:str)->str:
    """
    Deterministic ID based on content.
    Same content always gets same ID, so re-ingesting
    the same
    """
    raw = f"{source}|{section}|{strategy}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def heading_chunk(text:str, source:str, doc_meta:Dict) -> List[Chunk]:
    """
    Splits Markdown text into chunks based on ## headings.
    Each chunk is a section of the document.
    """
    pattern = re.compile(r"^##\s+(.*)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        cid = _make_chunk_id(source, "full_doc", text)
        return [Chunk(
            chunk_id=cid,
            text=text,
            source=source,
            section="full_doc",
            strategy="heading_chunk",
            metadata=doc_meta,
        )]
    
    chunks=[]
    for i,match in enumerate(matches):
        section_title = match.group(1).strip()
        start = match.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        if not section_text:
            continue
        cid = _make_chunk_id(source, section_title, section_text)

        chunks.append(Chunk(
            chunk_id=cid,
            text=section_text,
            source=source,
            section=section_title,
            strategy="heading_chunk",
            metadata=doc_meta,
        ))
    return chunks

def fixed_chunk(text:str, source:str, doc_meta: Dict, window_words:int = 150, overlap_words:int = 30) -> List[Chunk]:
    """
    Splits text into fixed word-count windows with overlap.
    overlap_words means the last N words of one chunk
    are repeated at the start of the next — this prevents
    important context being split right at a boundary.
    """
    words = text.split()
    if not words:
        return []
    
    chunks=[]
    step = window_words - overlap_words
    for start in range(0, len(words), step):
        window = words[start : start + window_words]
        if not window:
            break
        chunk_text = " ".join(window)
        cid = _make_chunk_id(source, f"fixed_{start}", chunk_text)
        chunks.append(Chunk(
            chunk_id=cid,
            text=chunk_text,
            source=source,
            section=f"fixed_window_{start}",
            strategy="fixed",
            metadata=doc_meta,
        ))
        
        if start + window_words >= len(words):
            break  # No more words left for another chunk(end of document)
    return chunks

def chunk_document(text:str, source:str, doc_meta:Dict) -> List[Chunk]:
    """
    Runs BOTH strategies on the same document and returns
    the combined list. Each chunk is tagged with which
    strategy produced it so you can compare them later.
    """
    return heading_chunk(text, source, doc_meta) + fixed_chunk(text, source, doc_meta)