"""
Ingestion pipeline for the Support Knowledge Copilot.

Loads documents from data/docs/, extracts metadata, chunks them using
both strategies, embeds each chunk via Ollama, and indexes them into:
  - Qdrant (dense/vector search)
  - A local BM25 index (sparse/keyword search), saved to disk

Run with:
    python -m src.ingest --source data/docs --rebuild
"""

import os
import json
import pickle
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime


import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from rank_bm25 import BM25Okapi

from src.chunking import chunk_document, Chunk

EMBED_MODEL = "nomic-embed-text"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "support_knowledge_copilot"
BM25_INDEX_PATH = "data/bm25_index.pkl"
EMBED_DIM = 768

def clean_text(text: str) -> str:
    """
    Removes metadata header lines from doc text before chunking.
    Keeps only actual content.
    """
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        lower = line.lower().strip()
        if lower.startswith("last updated:"):
            continue
        if lower.startswith("access level:"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def load_documents(source_dir: str):
    """Reads all .md/.txt files in source_dir, returns (text, source_name, doc_meta)."""

    
    docs = []
    source_path = Path(source_dir)
    for file_path in source_path.glob("*.md"):
        text = file_path.read_text(encoding="utf-8")
        

        last_updated = None
        access_level = None
        for line in text.splitlines():
            if line.lower().startswith("last updated:"):
                last_updated = line.split(":",1)[1].strip()
            if line.lower().startswith("access level:"):
                access_level = line.split(":",1)[1].strip()

        text = clean_text(text) 
        
        doc_meta ={
            
            "source": file_path.name,
            "doc_type": file_path.suffix[1:],  # 'md' 
            "last_updated": last_updated,
            "access_level": access_level,   
            "ingested_at" : datetime.utcnow().isoformat()

            }
        docs.append((text,file_path.name, doc_meta))
    return docs

def embed_texts (text:str) -> list:
    """Embeds a list of texts using Ollama."""
    response = ollama.embeddings(model=EMBED_MODEL, prompt= text)
    return response["embedding"]

def setup_qdrant_colection(client: QdrantClient, rebuild:bool):
    if rebuild and client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
        )
    
def ingest(source_dir:str, rebuild:bool):
    """Main ingestion function."""
    print(f"Loading documents from {source_dir}.....")
    docs = load_documents(source_dir)
    print(f"Found {len(docs)} documents. \n Chunking and embedding...")

    all_chunks = []
    for text,source,doc_meata in docs:
        chunks = chunk_document(text, source, doc_meata)
        all_chunks.extend(chunks)
    print(f"Total chunks created: {len(all_chunks)}. \n Embedding and indexing...")

    # Dense index(Qdrant)
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    setup_qdrant_colection(client, rebuild)
    points = []
    for i,chunk in enumerate(all_chunks):
        print(f"  Embedding chunk {i+1}/{len(all_chunks)}: {chunk.chunk_id}...")
        vector = embed_texts(chunk.text)
        points.append(PointStruct(
            id=i,
            vector=vector,
            payload={
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "source": chunk.source,
                "section": chunk.section,
                "strategy": chunk.strategy,
                **chunk.metadata,
            },
        ))
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Qdrant indexing complete. {len(points)} points upserted to collection '{COLLECTION_NAME}'.")

    #Sparse index (BM25)
    bm25_corpus = [chunk.text.lower().split() for chunk in all_chunks]
    bm25 = BM25Okapi(bm25_corpus)

    os.makedirs(os.path.dirname(BM25_INDEX_PATH), exist_ok=True)
    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump({
            "bm25":bm25,
            "chunks" :[
                {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "source": chunk.source,
                    "section": chunk.section,
                    "strategy": chunk.strategy,
                    **chunk.metadata,
                }
                for chunk in all_chunks
            ]
        },f)
    print(f"BM25 index saved to {BM25_INDEX_PATH}.")
    print("Ingestion complete. Both dense and sparse indexes are ready for querying.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into Qdrant and BM25 index.")
    parser.add_argument("--source", type=str, default="data/docs", help="Directory containing documents to ingest.")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the Qdrant collection if it exists.")
    args = parser.parse_args()

    ingest(args.source, args.rebuild)




   