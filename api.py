"""
FastAPI service for the Support Knowledge Copilot.

Exposes the full RAG pipeline as an HTTP API.
Run with:
    uvicorn api:app --reload

Then open:
    http://localhost:8000/docs  ← Swagger UI to test endpoints
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.retrieval import hybrid_retrieve
from src.generation import generate_answer, verify_citations
from src.confidence import compute_confidence

app = FastAPI(
    title="Support Knowledge Copilot API",
    description="RAG system with hybrid retrieval and verified citations",
    version="1.0.0"
)


# ── Request model ────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str
    use_hybrid: bool = True
    use_reranker: bool = True
    top_k: int = 10
    final_n: int = 5

    class Config:
        json_schema_extra = {
            "example": {
                "question": "How do I reset my password?",
                "use_hybrid": True,
                "use_reranker": True,
                "top_k": 10,
                "final_n": 5
            }
        }


# ── Response models ──────────────────────────────────────────────────────────

class CitationVerdict(BaseModel):
    chunk_id: str
    verdict: str

class RetrievedChunk(BaseModel):
    chunk_id: str
    source: str
    section: str
    strategy: str
    
class ConfidenceBreakdown(BaseModel):
    retrieval_score: float
    citation_support_rate: float
    completeness_score: float
    declared_no_answer: bool

class ConfidenceResult(BaseModel):
    final_confidence: float
    breakdown: ConfidenceBreakdown

class ChunkDetail(BaseModel):
    chunk_id: str
    text: str
    source: str
    section: str
    strategy: str
    score: float
    fused_score: float = 0.0
    rerank_score: float = 0.0
    last_updated: str = "unknown"
    access_level: str = "unknown"
    ingested_at: str = ""

class AskResponse(BaseModel):
    question: str
    answer: str
    cited_chunk_ids: list[str]
    citation_verdicts: list[CitationVerdict]
    citation_support_rate: float
    confidence: ConfidenceResult
    retrieved_chunks: list[RetrievedChunk]
    retrieval_mode: str
    debug: dict


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """
    Health check endpoint.
    Returns ok if the service is running.
    """
    return {"status": "ok", "service": "Support Knowledge Copilot"}


@app.post("/ask", response_model=AskResponse)
def ask(request: QuestionRequest):
    """
    Main RAG endpoint.
    Takes a question and returns a grounded answer with citations,
    citation verdicts, and a confidence score.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Step 1 — Retrieval
        sparse_weight = 1.0 if request.use_hybrid else 0.0
        retrieval_results = hybrid_retrieve(
            request.question,
            top_k=request.top_k,
            sparse_weight=sparse_weight,
            use_reranker=request.use_reranker,
            final_n=request.final_n,
        )

        # Step 2 — Generation
        gen_result = generate_answer(
            request.question,
            retrieval_results["final_results"]
        )

        # Step 3 — Citation verification
        citation_check = verify_citations(
            gen_result["answer"],
            retrieval_results["final_results"]
        )

        # Step 4 — Confidence scoring
        confidence = compute_confidence(
            retrieval_results,
            citation_check,
            gen_result["answer"]
        )

        # Step 5 — Build response
        retrieval_mode = "hybrid" if request.use_hybrid else "dense_only"

        return AskResponse(
            question=request.question,
            answer=gen_result["answer"],
            cited_chunk_ids=gen_result["cited_chunk_ids"],
            citation_verdicts=[
                CitationVerdict(
                    chunk_id=v["chunk_id"],
                    verdict=v["verdict"]
                )
                for v in citation_check["verdicts"]
            ],
            citation_support_rate=float(citation_check["citation_support_rate"]),
            confidence=ConfidenceResult(
                final_confidence=float(confidence["final_confidence"]),
                breakdown=ConfidenceBreakdown(
                    retrieval_score=float(confidence["breakdown"]["retrieval_score"]),
                    citation_support_rate=float(confidence["breakdown"]["citation_support_rate"]),
                    completeness_score=float(confidence["breakdown"]["completeness_score"]),
                    declared_no_answer=bool(confidence["breakdown"]["declared_no_answer"]),
                )
            ),
            retrieved_chunks=[
                RetrievedChunk(
                    chunk_id=c["chunk_id"],
                    source=c["source"],
                    section=c["section"],
                    strategy=c.get("strategy", "unknown"),
                    text=c.get("text", ""),
                )
                for c in retrieval_results["final_results"]
            ],
            retrieval_mode=retrieval_mode,
            debug={
                "dense_results": [
                    {
                        "chunk_id": r["chunk_id"],
                        "text": r["text"],
                        "source": r["source"],
                        "section": r["section"],
                        "strategy": r.get("strategy", r.get("payload", {}).get("strategy", "unknown")),
                        "score": round(float(r["score"]), 6),
                        "last_updated": r.get("payload", {}).get("last_updated", "unknown"),
                        "access_level": r.get("payload", {}).get("access_level", "unknown"),
                        "ingested_at": r.get("payload", {}).get("ingested_at", ""),
                    }
                    for r in retrieval_results["dense_results"]
                ],
                "sparse_results": [
                    {
                        "chunk_id": r["chunk_id"],
                        "text": r["text"],
                        "source": r["source"],
                        "section": r["section"],
                        "strategy": r.get("strategy", r.get("payload", {}).get("strategy", "unknown")),
                        "score": round(float(r["score"]), 6),
                        "last_updated": r.get("payload", {}).get("last_updated", "unknown"),
                        "access_level": r.get("payload", {}).get("access_level", "unknown"),
                        "ingested_at": r.get("payload", {}).get("ingested_at", ""),
                    }
                    for r in retrieval_results["sparse_results"]
                ],
                "fused_results": [
                    {
                        "chunk_id": r["chunk_id"],
                        "text": r["text"],
                        "source": r["source"],
                        "section": r["section"],
                        "strategy": r.get("strategy", r.get("payload", {}).get("strategy", "unknown")),
                        "score": round(float(r.get("score", 0)), 6),
                        "fused_score": round(float(r.get("fused_score", 0)), 8),
                        "last_updated": r.get("payload", {}).get("last_updated", "unknown"),
                        "access_level": r.get("payload", {}).get("access_level", "unknown"),
                        "ingested_at": r.get("payload", {}).get("ingested_at", ""),
                    }
                    for r in retrieval_results["fused_results"]
                ],
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chunks")
def list_chunks():
    """
    Debug endpoint — lists all chunks stored in the BM25 index.
    Useful for verifying ingestion worked correctly.
    """
    import pickle
    try:
        with open("data/bm25_index.pkl", "rb") as f:
            data = pickle.load(f)
        chunks = data["chunks"]
        return {
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "chunk_id": c["chunk_id"],
                    "source": c["source"],
                    "section": c["section"],
                    "strategy": c["strategy"],
                    "text_preview": c["text"][:100] + "..."
                }
                for c in chunks
            ]
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="BM25 index not found. Run ingestion first: python -m src.ingest --source data/docs"
        )


@app.get("/sources")
def list_sources():
    """
    Lists all unique source documents that have been ingested.
    """
    import pickle
    try:
        with open("data/bm25_index.pkl", "rb") as f:
            data = pickle.load(f)
        chunks = data["chunks"]
        sources = {}
        for c in chunks:
            src = c["source"]
            if src not in sources:
                sources[src] = {
                    "source": src,
                    "chunk_count": 0,
                    "strategies": set(),
                    "last_updated": c.get("last_updated", "unknown"),
                    "access_level": c.get("access_level", "unknown"),
                }
            sources[src]["chunk_count"] += 1
            sources[src]["strategies"].add(c["strategy"])

        return {
            "total_sources": len(sources),
            "sources": [
                {
                    **v,
                    "strategies": list(v["strategies"])
                }
                for v in sources.values()
            ]
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="BM25 index not found. Run ingestion first."
        )