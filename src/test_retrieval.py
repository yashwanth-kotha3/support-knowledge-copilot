from src.retrieval import hybrid_retrieve

query = "How do I reset my password?"
print(f"\nQuery: {query}")
print("="*60)

results = hybrid_retrieve(query, use_reranker=False)

print("\n--- DENSE RESULTS (top 3) ---")
for i, r in enumerate(results["dense_results"][:3]):
    print(f"{i+1}. [{r['source']}] {r['section']}")
    print(f"   Score: {r['score']:.4f}")

print("\n--- SPARSE RESULTS ---")
if results["sparse_results"]:
    for i, r in enumerate(results["sparse_results"][:3]):
        print(f"{i+1}. [{r['source']}] {r['section']}")
        print(f"   BM25 Score: {r['score']:.4f}")
else:
    print("No sparse results (no keyword matches)")

print("\n--- FUSED RESULTS (top 3) ---")
for i, r in enumerate(results["fused_results"][:3]):
    print(f"{i+1}. [{r['source']}] {r['section']}")
    print(f"   Fused Score: {r['fused_score']:.5f}")

print("\n--- FINAL RESULTS (top 5, no reranker) ---")
for i, r in enumerate(results["final_results"]):
    print(f"{i+1}. [{r['source']}] {r['section']}")