"""
Evaluation suite. Runs the golden Q&A set through the pipeline and
generates a Markdown report comparing dense-only vs hybrid retrieval.

Run with:
    python -m src.eval --strategy hybrid
"""

import json
import argparse
from datetime import datetime

from src.retrieval import hybrid_retrieve
from src.generation import generate_answer, verify_citations
from src.confidence import compute_confidence


def load_golden_set(path: str = "golden_qa.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_single(question_item: dict, strategy: str):
    question = question_item["question"]

    if strategy == "dense_only":
        retrieval_results = hybrid_retrieve(question, sparse_weight=0.0, use_reranker=False)
    else:
        retrieval_results = hybrid_retrieve(question, use_reranker=True)

    gen_result = generate_answer(question, retrieval_results["final_results"])
    citation_check = verify_citations(gen_result["answer"], retrieval_results["final_results"])
    confidence = compute_confidence(retrieval_results, citation_check, gen_result["answer"])

    retrieved_sources = {c["source"] for c in retrieval_results["final_results"]}
    expected_sources = set(question_item.get("expected_sources", []))
    correct_retrieval = bool(expected_sources & retrieved_sources) if expected_sources else None

    return {
        "question": question,
        "answer": gen_result["answer"],
        "retrieved_sources": list(retrieved_sources),
        "expected_sources": list(expected_sources),
        "correct_retrieval": correct_retrieval,
        "citation_support_rate": citation_check["citation_support_rate"],
        "confidence": confidence["final_confidence"],
        "confidence_breakdown": confidence["breakdown"],
        "is_no_answer_case": question_item.get("no_answer_expected", False),
    }


def run_eval(strategy: str):
    golden_set = load_golden_set()
    results = []

    for i, item in enumerate(golden_set):
        print(f"Running {i + 1}/{len(golden_set)}: {item['question'][:60]}...")
        results.append(run_single(item, strategy))

    retrieval_judged = [r for r in results if r["correct_retrieval"] is not None]
    correct_retrieval_rate = (
        sum(1 for r in retrieval_judged if r["correct_retrieval"]) / len(retrieval_judged)
        if retrieval_judged else 0.0
    )

    rates = [float(r["citation_support_rate"]) for r in results]
    avg_citation_support = sum(rates) / len(rates) if rates else 0.0

    avg_confidence = sum(float(r["confidence"]) for r in results) / len(results) if results else 0.0

    no_answer_cases = [r for r in results if r["is_no_answer_case"]]
    correct_refusals = sum(
        1 for r in no_answer_cases
        if "i could not find this in the docs" in r["answer"].lower()
    )
    refusal_accuracy = correct_refusals / len(no_answer_cases) if no_answer_cases else None

    report = generate_report(
        strategy, results, correct_retrieval_rate,
        avg_citation_support, avg_confidence, refusal_accuracy
    )

    out_path = f"eval_report_{strategy}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nEval complete. Report saved to {out_path}")
    print(f"Correct retrieval rate: {correct_retrieval_rate:.1%}")
    print(f"Avg citation support rate: {avg_citation_support:.1%}")
    print(f"Avg confidence: {avg_confidence:.3f}")
    if refusal_accuracy is not None:
        print(f"No-answer refusal accuracy: {refusal_accuracy:.1%}")


def generate_report(strategy, results, correct_retrieval_rate, avg_citation_support,
                    avg_confidence, refusal_accuracy):
    lines = [
        f"# Evaluation Report — strategy: {strategy}",
        f"Generated: {datetime.utcnow().isoformat()}",
        "",
        "## Summary Metrics",
        f"- Correct retrieval rate: {correct_retrieval_rate:.1%}",
        f"- Avg citation support rate: {avg_citation_support:.1%}",
        f"- Avg confidence score: {avg_confidence:.3f}",
    ]

    if refusal_accuracy is not None:
        lines.append(f"- No-answer refusal accuracy: {refusal_accuracy:.1%}")
    lines.append("")
    lines.append("## Per-Question Results")

    for r in results:
        lines.append(f"\n### Q: {r['question']}")
        lines.append(f"**Answer:** {r['answer']}")
        lines.append(f"- Retrieved sources: {r['retrieved_sources']}")
        lines.append(f"- Expected sources: {r['expected_sources']}")
        lines.append(f"- Correct retrieval: {r['correct_retrieval']}")
        lines.append(f"- Citation support rate: {float(r['citation_support_rate']):.1%}")
        lines.append(f"- Confidence: {r['confidence']} ({r['confidence_breakdown']})")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="hybrid", choices=["hybrid", "dense_only"])
    args = parser.parse_args()
    run_eval(args.strategy)