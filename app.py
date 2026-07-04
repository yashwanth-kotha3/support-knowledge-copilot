"""
Streamlit dashboard for the Support Knowledge Copilot.
Connected to FastAPI backend at http://127.0.0.1:8000

Run FastAPI first:
    uvicorn api:app --reload

Then run Streamlit:
    streamlit run app.py
"""

import streamlit as st
import requests
import os

# ── Config ───────────────────────────────────────────────────────────────────

API_URL = "https://support-copilot-api-4khe.onrender.com"

st.set_page_config(
    page_title="Support Knowledge Copilot",
    layout="wide"
)

st.title("Support Knowledge Copilot")
st.caption("RAG with Hybrid Retrieval and Verified Citations")

# ── Check FastAPI is running ──────────────────────────────────────────────────

try:
    health = requests.get(f"{API_URL}/health", timeout=2)
    if health.status_code == 200:
        st.sidebar.success("✅ API connected")
    else:
        st.sidebar.error("❌ API returned error")
except Exception:
    st.sidebar.error("❌ FastAPI not running. Start with: uvicorn api:app --reload")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:

    st.header("Retrieval Settings")

    use_hybrid = st.toggle(
        "Use hybrid retrieval (dense + sparse)",
        value=True
    )

    use_reranker = st.toggle(
        "Use LLM reranker",
        value=True
    )

    top_k = st.slider(
        "Top-K per retriever",
        min_value=3,
        max_value=20,
        value=10
    )

    final_n = st.slider(
        "Final chunks for generation",
        min_value=1,
        max_value=10,
        value=5
    )

    st.divider()

    # ── Sources panel ─────────────────────────────────────────────────────────

    st.header("Knowledge Base")

    if st.button("Show Sources"):
        try:
            resp = requests.get(f"{API_URL}/sources", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                st.write(f"Total sources: **{data['total_sources']}**")
                for s in data["sources"]:
                    st.write(
                        f"- **{s['source']}** "
                        f"({s['chunk_count']} chunks, "
                        f"{s['access_level']})"
                    )
            else:
                st.error("Could not fetch sources")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Upload new document ───────────────────────────────────────────────────

    st.header("Add Document")

    admin_password = st.text_input(
        "Admin password to upload:",
        type="password",
        help="Only admins can add documents to the knowledge base"
    )

    ADMIN_PASSWORD = "admin123"
    is_admin = admin_password == ADMIN_PASSWORD

    if admin_password and not is_admin:
        st.error("❌ Wrong password")

    if is_admin:
        st.success("✅ Admin access granted")

        uploaded_file = st.file_uploader(
            "Upload a markdown file",
            type=["md"],
            help="Upload a .md file to add to the shared knowledge base"
        )

        if uploaded_file is not None:
            if st.button("Ingest Document"):
                save_path = os.path.join("data", "docs", uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                with st.spinner(f"Ingesting {uploaded_file.name}..."):
                    from src.ingest import ingest
                    ingest("data/docs", rebuild=False)

                st.success(f"✅ {uploaded_file.name} added to knowledge base!")
                st.info("Ask a question about it below.")

# ── Main area ─────────────────────────────────────────────────────────────────

question = st.text_input("Ask a support question:")

if st.button("Submit") and question:

    payload = {
        "question": question,
        "use_hybrid": use_hybrid,
        "use_reranker": use_reranker,
        "top_k": top_k,
        "final_n": final_n
    }

    # ── Call FastAPI ──────────────────────────────────────────────────────────

    with st.spinner("Calling API..."):
        try:
            response = requests.post(
                f"{API_URL}/ask",
                json=payload,
                timeout=120
            )
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to FastAPI. Make sure uvicorn is running.")
            st.stop()

    if response.status_code != 200:
        st.error(f"API Error {response.status_code}: {response.text}")
        st.stop()

    result = response.json()

    # ── Answer ────────────────────────────────────────────────────────────────

    st.subheader("Answer")
    st.write(result["answer"])

    st.divider()

    col1, col2 = st.columns(2)

    # ── Left column ───────────────────────────────────────────────────────────

    with col1:

        st.subheader("Confidence Breakdown")

        confidence_value = result["confidence"]["final_confidence"]
        if confidence_value >= 0.7:
            st.metric("Final Confidence", confidence_value, delta="High")
        elif confidence_value >= 0.4:
            st.metric("Final Confidence", confidence_value, delta="Medium")
        else:
            st.metric("Final Confidence", confidence_value, delta="Low")

        st.json(result["confidence"]["breakdown"])

        st.subheader("Citation Verdicts")

        if result["citation_verdicts"]:
            for verdict in result["citation_verdicts"]:
                icon = "✅" if verdict["verdict"] == "supported" else "❌"
                st.write(
                    f"{icon} `{verdict['chunk_id']}` — {verdict['verdict']}"
                )
        else:
            st.write("No citations found in answer.")

        st.subheader("Retrieval Mode")
        mode = result["retrieval_mode"]
        if mode == "hybrid":
            st.success(f"Mode: {mode} (dense + sparse + RRF)")
        else:
            st.warning(f"Mode: {mode} (dense only)")

    # ── Right column ──────────────────────────────────────────────────────────

    with col2:

        st.subheader("Retrieved Chunks (Final)")

        for chunk in result["retrieved_chunks"]:
            with st.expander(
                f"{chunk['source']} — {chunk['section']}"
            ):
                display_text = chunk.get("text", "")
                clean_lines = [
                    line for line in display_text.splitlines()
                    if not line.strip().startswith("#")
                    and not line.lower().strip().startswith("last updated")
                    and not line.lower().strip().startswith("access level")
                ]
                st.write("\n".join(clean_lines))
                st.divider()
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**chunk_id:** `{chunk['chunk_id']}`")
                    st.write(f"**source:** {chunk['source']}")
                    st.write(f"**section:** {chunk['section']}")
                with col_b:
                    st.write(f"**strategy:** {chunk['strategy']}")

    # ── Full Debug Panel ──────────────────────────────────────────────────────

    st.divider()

    with st.expander("🔍 Debug: Full Retrieval Details"):

        debug = result.get("debug", {})

        tab1, tab2, tab3 = st.tabs([
            "Dense Results",
            "Sparse Results",
            "Fused Results"
        ])

        # ── Dense tab ────────────────────────────────────────────────────────

        with tab1:
            dense = debug.get("dense_results", [])
            st.write(f"**Dense results: {len(dense)} chunks**")
            st.caption("Ranked by cosine similarity — semantic search via Qdrant")

            for i, r in enumerate(dense):
                with st.expander(
                    f"Rank {i+1} | [{r['source']}] {r['section']} | score: {r['score']}"
                ):
                    st.write(f"**Text:**")
                    st.write(r["text"])
                    st.divider()
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**chunk_id:** `{r['chunk_id']}`")
                        st.write(f"**source:** {r['source']}")
                        st.write(f"**section:** {r['section']}")
                        st.write(f"**strategy:** {r['strategy']}")
                    with col_b:
                        st.write(f"**score:** {r['score']}")
                        st.write(f"**last_updated:** {r['last_updated']}")
                        st.write(f"**access_level:** {r['access_level']}")
                        st.write(f"**ingested_at:** {r['ingested_at']}")

        # ── Sparse tab ────────────────────────────────────────────────────────

        with tab2:
            sparse = debug.get("sparse_results", [])
            st.write(f"**Sparse results: {len(sparse)} chunks**")
            st.caption("Ranked by BM25 keyword score — exact term matching")

            if sparse:
                for i, r in enumerate(sparse):
                    with st.expander(
                        f"Rank {i+1} | [{r['source']}] {r['section']} | BM25 score: {r['score']}"
                    ):
                        st.write(f"**Text:**")
                        st.write(r["text"])
                        st.divider()
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**chunk_id:** `{r['chunk_id']}`")
                            st.write(f"**source:** {r['source']}")
                            st.write(f"**section:** {r['section']}")
                            st.write(f"**strategy:** {r['strategy']}")
                        with col_b:
                            st.write(f"**BM25 score:** {r['score']}")
                            st.write(f"**last_updated:** {r['last_updated']}")
                            st.write(f"**access_level:** {r['access_level']}")
                            st.write(f"**ingested_at:** {r['ingested_at']}")
            else:
                st.info("No sparse results — no keyword matches for this query.")

        # ── Fused tab ─────────────────────────────────────────────────────────

        with tab3:
            fused = debug.get("fused_results", [])
            st.write(f"**Fused results: {len(fused)} chunks**")
            st.caption("Ranked by RRF fusion score — dense + sparse combined")

            for i, r in enumerate(fused):
                with st.expander(
                    f"Rank {i+1} | [{r['source']}] {r['section']} | fused_score: {r['fused_score']}"
                ):
                    st.write(f"**Text:**")
                    st.write(r["text"])
                    st.divider()
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**chunk_id:** `{r['chunk_id']}`")
                        st.write(f"**source:** {r['source']}")
                        st.write(f"**section:** {r['section']}")
                        st.write(f"**strategy:** {r['strategy']}")
                    with col_b:
                        st.write(f"**raw score:** {r['score']}")
                        st.write(f"**fused_score:** {r['fused_score']}")
                        st.write(f"**last_updated:** {r['last_updated']}")
                        st.write(f"**access_level:** {r['access_level']}")
                        st.write(f"**ingested_at:** {r['ingested_at']}")