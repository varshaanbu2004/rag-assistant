import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st

st.set_page_config(page_title="Rural Scheme Advisor", page_icon="🌾")

_ROOT = Path(__file__).resolve().parent.parent
_chroma_dir = _ROOT / "chroma_db"
_build_script = _ROOT / "src" / "build_index.py"
_raw_dir = _ROOT / "data" / "raw"

if not (_chroma_dir.exists() and any(_chroma_dir.iterdir())):
    if not list(_raw_dir.glob("*.pdf")):
        st.error("No documents found in data/raw. Add the PDF files before starting the app.")
    else:
        with st.spinner("Index not found. Building from documents..."):
            subprocess.run([sys.executable, str(_build_script)], check=False, cwd=str(_ROOT))

from ask import ask
from hybrid import combined_retrieve
st.title("🌾 Rural Scheme Advisor")
st.caption("Ask about PM-KISAN or PMFBY. Answers come from official documents and show their sources. Please verify with the official portal (pmkisan.gov.in) before acting.")

scheme_choice = st.sidebar.selectbox("Scheme", ["Auto-detect", "PM-KISAN", "PMFBY"])
scheme = None if scheme_choice == "Auto-detect" else scheme_choice

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Type your question, e.g. How much money does PM-KISAN give?")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the documents..."):
            try:
                answer, hits = ask(
                    question,
                    retriever=lambda q: combined_retrieve(q, scheme=scheme),
                    return_hits=True
                )
            except Exception:
                st.error("The service is busy or unavailable. Please try again in a minute.")
                st.stop()

        st.markdown(answer)
        if hits:
            # Deduplicate by (source, page) so repeated chunks from merge don't spam the list
            seen, uniq = set(), []
            for _,meta in hits:
                key = (meta["source"], meta["page"] if meta["page"] == meta["page_end"] else f"{meta['page']}-{meta['page_end']}")
                if key not in seen:
                    seen.add(key)
                    uniq.append(meta)
            with st.expander("Passages retrieved (not all used in the answer)", expanded=False):
                for meta in uniq:
                    p = meta["page"] if meta["page"] == meta["page_end"] else f"{meta['page']}-{meta['page_end']}"
                    st.caption(f"- {meta['source']}, page {p}")
        st.caption("Documents are from 2020 and 2023. Verify on the official portal.")

    st.session_state.messages.append({"role": "assistant", "content": answer})