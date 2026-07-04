"""
Combines retrieval score, citation support rate, and no-answer detection
into a single confidence score with a breakdown.
"""

NO_ANSWER_PHRASE = "i could not find this in the docs"

def compute_confidence(retrival_results: dict, citation_check: dict, answer_text:str) -> dict:
    final_results = retrival_results["final_results"]

    if final_results:
        scores = [r.get("rerank_score", r.get("fusion_score",0)) for r in final_results]
        max_possible = 10.0 if "rerank_score" in final_results[0] else 1.0
        retrival_score = min(sum(scores) / len(scores) / max_possible, 1.0)
    else:
        retrival_score = 0.0
    
    citation_score = citation_check["citation_support_rate"]

    declared_no_answer = NO_ANSWER_PHRASE in answer_text.lower()

    has_citations = len(citation_check["verdicts"]) > 0
    completeness_score = 1.0 if (has_citations and not declared_no_answer) else(0.5 if declared_no_answer else 0.0)

    if declared_no_answer:
        final_confidence = 1.0 if retrival_score < 0.3 else 0.4
    else:
        final_confidence = (
            0.4 * retrival_score + 0.4 * citation_score + 0.2 *completeness_score
        )
    return {
        "final_confidence" : round(final_confidence,3),
        "breakdown" : {
            "retrieval_score":round(retrival_score,3),
            "citation_support_rate": round(citation_score, 3),
            "completeness_score": round(completeness_score, 3),
            "declared_no_answer": declared_no_answer,
        },
    }
