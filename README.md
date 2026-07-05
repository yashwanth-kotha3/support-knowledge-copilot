# Support Knowledge Copilot

> Production-style enterprise RAG system with hybrid retrieval and verified citations

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39.0-FF4B4B?style=flat&logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python)](https://python.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.12.0-DC143C?style=flat&logo=qdrant)](https://qdrant.tech)

---

## 🔗 Live Links

| Service                  | URL                                                           |
| ------------------------ | ------------------------------------------------------------- |
| 📡 API docs (Swagger UI) | https://support-copilot-api-4khe.onrender.com/docs            |
| 🎯 Streamlit dashboard   | https://support-knowledge-copilot-nbeaentnhuuu.streamlit.app  |
| 🐙 GitHub                | https://github.com/yashwanth-kotha3/support-knowledge-copilot |

---

## 🏢 What Is This

A Support Knowledge Copilot for enterprise documentation. Administrators
ingest and control internal knowledge documents through a password-protected
interface. Employees query the shared knowledge base through a hybrid
retrieval pipeline and receive grounded answers with verified citations.

This is not a tutorial follow-along. Every line was written, debugged,
and understood from scratch — no LangChain, no LangGraph.

---

## 📊 Eval Results

Strategy Correct Retrieval Refusal Accuracy
──────────────────────────────────────────────────────
Hybrid (RRF) 100% 100%
Dense only 75% 100%

Hybrid retrieval improved correct-source retrieval from 75% to 100%
on a 5-question golden evaluation set.

---

## 🏗️ Architecture

Administrator uploads docs
↓
Document loading + metadata extraction
↓
Two chunking strategies simultaneously:

Heading-based (preserves structure)
Fixed-window 150 words, 30 overlap
↓
Embed with nomic-embed-text (768-dim)
↓
Dual indexing:
Qdrant (dense vector search)
BM25 (sparse keyword search)
↓
Employee asks question
↓
Hybrid retrieval:
Dense search (cosine similarity)

- Sparse search (BM25 keywords)
  ↓
  Reciprocal Rank Fusion (RRF)
  ↓
  LLM Reranker (scores 0-10)
  ↓
  Top 5 chunks → LLM generation
  (strict prompt: cite everything,
  refuse if answer not in docs)
  ↓
  Citation verification
  (second LLM call per citation)
  ↓
  Confidence scoring
  (retrieval 40% + citations 40%

completeness 20%)
↓
Answer + verdicts + confidence returned

---

## ⚙️ Key Engineering Decisions

**Why hybrid retrieval?**
Dense search understands meaning but misses exact terms — error codes
like AUTH*401, API prefixes like sk_live*, version numbers. BM25 catches
these with precision. Together they cover both failure modes. Proved by
eval: dense-only 75%, hybrid 100%.

**Why Reciprocal Rank Fusion?**
Dense scores (0-1) and BM25 scores (0-12+) live in different spaces.
You cannot average them. RRF uses rank position — `1/(k+rank)` — which
is scale-invariant. Chunks in both lists accumulate from both and get
boosted. K=60 is the research-recommended standard.

**Why verify citations?**
LLMs hallucinate citations. A chunk ID in an answer means nothing unless
you confirm the chunk supports the claim. A second LLM call per citation
is the difference between a RAG demo and a production RAG system.

**Why no LangChain?**
LangChain abstracts away exactly what interviewers test. Building from
scratch means every component is explainable in detail — chunking logic,
fusion math, citation verification, confidence weighting.

**Why FastAPI and Streamlit?**
Streamlit is for humans. FastAPI is for machines. In production a React
frontend or mobile app calls the API — not a Streamlit page. Having both
shows product thinking (UI) and engineering thinking (API) separately.

---

## 🛠️ Tech Stack

| Category        | Tool             | Reason                           |
| --------------- | ---------------- | -------------------------------- |
| Language        | Python 3.11      | Strong AI/ML ecosystem           |
| Embeddings      | nomic-embed-text | 768-dim, free, runs via Ollama   |
| LLM             | llama3.2         | Runs locally, zero API cost      |
| Vector DB       | Qdrant           | Local Docker, metadata filtering |
| Sparse Search   | BM25 (rank-bm25) | Catches exact terms dense misses |
| API             | FastAPI          | Production REST API + Swagger UI |
| Frontend        | Streamlit        | Interactive dashboard            |
| Containers      | Docker           | Runs Qdrant locally              |
| Version Control | Git + GitHub     | Full history, public repo        |
| API Deploy      | Render           | FastAPI live in cloud            |
| UI Deploy       | Streamlit Cloud  | Dashboard live in cloud          |

---

## 🖥️ Local Setup — Full Pipeline

The complete pipeline runs locally with zero API costs.

### Requirements

- Python 3.11
- Docker Desktop
- Ollama
- Git

### Step 1: Clone the repository

```bash
git clone https://github.com/yashwanth-kotha3/support-knowledge-copilot
cd support-knowledge-copilot
```

### Step 2: Create virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Pull Ollama models

```bash
ollama pull nomic-embed-text
ollama pull llama3.2
```

### Step 5: Start Qdrant via Docker

```bash
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

Windows PowerShell:

```powershell
docker run -d -p 6333:6333 -p 6334:6334 `
  -v ${PWD}/qdrant_storage:/qdrant/storage `
  qdrant/qdrant
```

### Step 6: Ingest documents

```bash
python -m src.ingest --source data/docs
```

Expected output:
Found 9 documents.
Total chunks to index: ~35
Ingestion complete.

### Step 7: Start FastAPI

```bash
uvicorn api:app --reload
```

API running at: `http://localhost:8000`
Swagger UI at: `http://localhost:8000/docs`

### Step 8: Start Streamlit (new terminal)

```bash
streamlit run app.py
```

Dashboard at: `http://localhost:8501`

---

## 🔑 Admin Upload

In the Streamlit sidebar, enter the admin password to unlock document upload.

Default password: `admin123`

Change this in `app.py`:

```python
ADMIN_PASSWORD = "admin123"  # change this
```

---

## 📊 Run Evaluation

```bash
# Hybrid retrieval
python -m src.eval --strategy hybrid

# Dense only (for comparison)
python -m src.eval --strategy dense_only
```

Reports saved to:

- `eval_report_hybrid.md`
- `eval_report_dense_only.md`

---

## 📁 Project Structure

support-knowledge-copilot/
├── src/
│ ├── init.py
│ ├── chunking.py # heading + fixed window strategies
│ ├── ingest.py # document loading, embedding, indexing
│ ├── retrieval.py # dense + sparse + RRF + reranker
│ ├── generation.py # grounded generation + citation verification
│ ├── confidence.py # confidence scoring
│ └── eval.py # evaluation suite + markdown reports
├── data/
│ └── docs/ # enterprise knowledge base documents
│ ├── password_reset.md
│ ├── api_auth.md
│ ├── billing.md
│ ├── api_guide.md
├── app.py # Streamlit dashboard
├── api.py # FastAPI REST API
├── golden_qa.json # evaluation question set
├── eval_report_hybrid.md
├── eval_report_dense_only.md
├── requirements.txt
├── .python-version
├── runtime.txt
└── README.md

---

## 🌐 API Endpoints

| Method | Endpoint   | Description                                             |
| ------ | ---------- | ------------------------------------------------------- |
| GET    | `/health`  | Health check — returns 200 if running                   |
| POST   | `/ask`     | Full RAG pipeline — question in, answer + citations out |
| GET    | `/chunks`  | Lists all ingested chunks                               |
| GET    | `/sources` | Lists all source documents                              |

### Example request

```bash
curl -X POST https://support-copilot-api-4khe.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I reset my password?",
    "use_hybrid": true,
    "use_reranker": true,
    "top_k": 10,
    "final_n": 5
  }'
```

### Example response

```json
{
  "question": "How do I reset my password?",
  "answer": "Go to Settings > Security and click Reset Password [chunk_id]. Links expire after 30 minutes [chunk_id].",
  "cited_chunk_ids": ["abc123", "def456"],
  "citation_verdicts": [
    { "chunk_id": "abc123", "verdict": "supported" },
    { "chunk_id": "def456", "verdict": "supported" }
  ],
  "citation_support_rate": 1.0,
  "confidence": {
    "final_confidence": 0.84,
    "breakdown": {
      "retrieval_score": 0.73,
      "citation_support_rate": 1.0,
      "completeness_score": 1.0,
      "declared_no_answer": false
    }
  },
  "retrieval_mode": "hybrid"
}
```

---

## ☁️ Cloud Deployment Note

The FastAPI is deployed on Render and Streamlit on Streamlit Cloud.
The full pipeline (LLM + vector search) runs locally via Ollama and
Qdrant. For full cloud operation:
Local Qdrant → Qdrant Cloud (cloud.qdrant.io)
Ollama → OpenAI API (text-embedding-3-small + gpt-4o-mini)

Both are environment variable changes only. Architecture stays identical.

---

## 💡 What I Learned

- How RAG systems fail in production and how to measure it
- Why hybrid retrieval beats dense-only for exact term queries
- How RRF works mathematically vs score normalization
- How to verify citations using LLM-as-judge
- How to build confidence scoring from multiple weak signals
- How to separate UI layer from API layer properly
- How to write a golden eval set and measure retrieval separately from answer quality
- Why building core logic from scratch beats frameworks for deep understanding

---

## 👤 Author

**Yashwanth Kotha**

- GitHub: [@yashwanth-kotha3](https://github.com/yashwanth-kotha3)
