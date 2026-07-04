# Support Knowledge Copilot

A production-style RAG system for enterprise documentation.

## What it does

- Administrators upload internal knowledge documents
- Employees query the shared knowledge base
- Hybrid retrieval: dense (Qdrant) + sparse (BM25) + RRF fusion
- Grounded answers with verified citations
- Confidence scoring on every response

## Results

- Correct retrieval rate: 100% (hybrid)
- No-answer refusal accuracy: 100%

## Stack

- Embeddings: nomic-embed-text (Ollama)
- LLM: llama3.2 (Ollama)
- Vector DB: Qdrant (Docker)
- Sparse search: BM25
- API: FastAPI
- UI: Streamlit

## Run locally

### Start services

```powershell
ollama pull nomic-embed-text
ollama pull llama3.2
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### Install dependencies

```powershell
pip install -r requirements.txt
```

### Ingest documents

```powershell
python -m src.ingest --source data/docs
```

### Run API

```powershell
uvicorn api:app --reload
```

### Run dashboard

```powershell
streamlit run app.py
```

## Eval

```powershell
python -m src.eval --strategy hybrid
python -m src.eval --strategy dense_only
```
