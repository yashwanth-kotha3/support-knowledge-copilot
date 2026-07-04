"""
Grounded answer generation: builds a strict prompt that forces the model
to answer only from retrieved context and cite chunk IDs.
"""

import re
import ollama

LLM_MODEL = "llama3.2"
ANSWER_PROMPT_TEMPLATE =  """
You are a support assistant. Answer the user's question using ONLY the context below.

Rules:
- Only use facts present in the context. Do not use outside knowledge.
- After every claim, cite the chunk ID it came from in square brackets, like [chunk_id].
- If the context does not contain enough information to answer, say exactly: "I could not find this in the docs."
- Be concise and direct.

Context:
{context}

Question: {question}

Answer:"""

def build_context(chunks:list)->str:
    blocks=[]
    for c in chunks:
        blocks.append(f"[ {c['chunk_id']}] (source: {c['source']}, section: {c['section']} ) \n {c['text']}  ")
    return "\n\n---\n\n".join(blocks)

def generate_answer(question:str, chunks:list)-> dict:
    context = build_context(chunks)
    prompt = ANSWER_PROMPT_TEMPLATE.format(context=context,question=question)

    response = ollama.generate(model=LLM_MODEL, prompt=prompt)
    answer_text = response["response"].strip()

    cited_ids = re.findall(r"\[([a-f0-9]{16})\]", answer_text)

    return {
        "answer": answer_text,
        "cited_chunk_ids": list(set(cited_ids)),
        "context_chunk_ids": [c["chunk_id"] for c in chunks],
    }

def verify_citations(answer_text:str, chunks:list ) ->dict:
    """
    For each cited chunk_id, checks whether the chunk actually exists in
    the retrieved context (basic check) and asks the LLM whether the
    chunk's text supports the specific claim near that citation (semantic check).
    """
    chunk_lookup = { c['chunk_id'] : c for c in chunks}
    cited_ids = re.findall(r"\[([a-f0-9]{16})\]", answer_text)

    verdicts=[]
    for cid in set(cited_ids):
        if cid not in chunk_lookup:
            verdicts.append({"chunk_id": cid, "verdict": "invalid_id", "reason": "Chunk ID not in retrieved context"})
            continue

        chunk_text = chunk_lookup[cid]["text"]
        verify_prompt = (
            f"I will show you a passage and a claim. "
            f"Tell me if the passage contains information that supports the claim.\n\n"
            f"Passage: {chunk_text}\n\n"
            f"Claim: {answer_text[:300]}\n\n"
            f"Does the passage support the claim? "
            f"Reply with YES or NO only, nothing else."
        )
        try:
            response = ollama.generate(model=LLM_MODEL, prompt=verify_prompt)
            verdict_text = response.response.strip().upper()
            verdict = "supported" if "YES" in verdict_text else "unsupported"
        except Exception:
            verdict = "error"
        verdicts.append({"chunk_id" : cid, "verdict" : verdict})
        

    support_count = sum(1 for v in verdicts if v["verdict"]=="supported")
    support_rate = support_count / len(verdicts) if verdicts else 0.0

    return {"verdicts":verdicts, "citation_support_rate":support_rate}


