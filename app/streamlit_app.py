import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st
from ask import ask

st.set_page_config(page_title="Rural Scheme Advisor", page_icon="🌾")
st.title("🌾 Rural Scheme Advisor")
st.caption("Ask about PM-KISAN. Answers come from official documents and show their sources. Please verify with the official portal (pmkisan.gov.in) before acting.")

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
                answer = ask(question)
            except Exception as e:
                answer = "Sorry, the AI service is busy or unavailable. Please try again in a minute."
                st.caption(f"Technical detail: {e}")
        st.markdown(answer)
        st.caption("Please verify with the official portal (pmkisan.gov.in) before acting.")

    st.session_state.messages.append({"role": "assistant", "content": answer})