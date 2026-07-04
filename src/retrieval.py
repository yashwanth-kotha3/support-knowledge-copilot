"""
Hybrid retrieval: dense (Qdrant) + sparse (BM25), fused with Reciprocal Rank Fusion (RRF),
then reranked using the local LLM as a lightweight reranker.
"""

import pickle
import ollama
from qdrant_client import QdrantClient

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "support_knowledge_copilot"
BM25_INDEX_PATH = "data/bm25_index.pkl"

RRF_K = 60  # standard RRF constant


def embed_query(query:str) ->list:
    response = ollama.embeddings(model=EMBED_MODEL, prompt=query)
    return response["embedding"]

def dense_search(query:str, top_k:int = 10):
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    vector = embed_query(query)
    results = client.query_points(collection_name=COLLECTION_NAME, query=vector,limit=top_k).points

    return [
        {
            "chunk_id": r.payload.get("chunk_id"),
            "text": r.payload.get("text"),
            "source": r.payload.get("source"),
            "section": r.payload.get("section"),
            "score": r.score,
            "payload": r.payload,
        }
        for r in results
    ]


def sparse_search(query:str, top_k:int = 10):
    with open(BM25_INDEX_PATH, "rb") as f:
        data=pickle.load(f)
    bm25=data["bm25"]
    chunks=data["chunks"]

    token_query = query.lower().split()
    scores = bm25.get_scores(token_query)
    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [
        {
            "chunk_id": chunk.get("chunk_id"),
            "text": chunk.get("text"),
            "source": chunk.get("source"),
            "section": chunk.get("section"),
            "score": float(score),
            "payload": chunk,
        }
        for chunk, score in ranked
        if score > 0
    ]

def reciprocal_rank_fusion(dense_results, sparse_results, dense_weight=1.0, sparse_weight=1.0):
    """
    Merges two ranked lists of results using Reciprocal Rank Fusion (RRF).
    RFF: score = weight * 1 / (k + rank), where k is a constant (RRF_K) and rank is the position in the list.

    """

    fused_scores = {}
    chunk_lookup = {}

    for rank,item in enumerate(dense_results):
        cid = item["chunk_id"]
        fused_scores[cid] = fused_scores.get(cid,0)+dense_weight * 1 / (RRF_K + rank+1)
        chunk_lookup[cid] =item
    
    for rank,item in enumerate(sparse_results):
        cid = item["chunk_id"]
        fused_scores[cid] = fused_scores.get(cid,0)+sparse_weight * 1 / (RRF_K + rank+1)
        chunk_lookup[cid] =item
    
    fused = sorted(fused_scores.items(), key=lambda x:x[1], reverse=True)

    return [{ **chunk_lookup[cid], "fused_score": score} for cid, score in fused]

def llm_rerank(query:str, fused_results:list, top_k:int = 10):
    """
    Reranks the fused results using the local LLM as a lightweight reranker.
    The LLM is prompted to score each chunk for relevance to the query.
    fused results chunk's relevance to the query on a 0-10 scale.
    """

    scored=[]
    for i in fused_results:
        prompt = (
            f"Question: {query}\n\n"
            f"Passage: {i['text'][:500]}\n\n"
            "On a scale of 0-10, how relevant is this passage to answering the question? "
            "Reply with ONLY a number, nothing else."
        )
        try:
            response = ollama.generate(model=LLM_MODEL, prompt=prompt)
            score_text = response["response"].strip()
            score = float("".join(ch for ch in score_text if ch.isdigit() or ch == '.'))
        except:
            score=0.0

        scored.append({**i, "rerank_score": score})

    scored.sort(key=lambda x: x["rerank_score"], reverse=True)
    return scored[:top_k]

def hybrid_retrieve(query: str, top_k: int = 10, dense_weight: float = 1.0,
                     sparse_weight: float = 1.0, use_reranker: bool = True, final_n: int = 5):
    
    dense_results = dense_search(query,top_k=top_k)
    sparse_results = sparse_search(query,top_k=top_k)
    
    fused = reciprocal_rank_fusion (dense_results, sparse_results, dense_weight, sparse_weight )

    if use_reranker:
        final = llm_rerank(query, fused, top_k=final_n)
    else:
        final = fused[:final_n]
    
    return {
        "dense_results" : dense_results,
        "sparse_results": sparse_results,
        "fused_results": fused,
        "final_results": final,
    }
   
