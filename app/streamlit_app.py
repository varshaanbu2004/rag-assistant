import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st
from ask import ask
from hybrid import combined_retrieve

st.set_page_config(page_title="Rural Scheme Advisor", page_icon="🌾")
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
            st.caption("Cited sources:")
            for _, meta in hits:
                p = meta["page"] if meta["page"] == meta["page_end"] else f"{meta['page']}-{meta['page_end']}"
                st.caption(f"- {meta['source']}, page {p}")
        st.caption("Documents are from 2020 and 2023. Verify on the official portal.")

    st.session_state.messages.append({"role": "assistant", "content": answer})