import streamlit as st
from rag_chat import get_chain, ask

st.set_page_config(page_title="Contract-Bot MVP", page_icon="1", layout="wide")
st.title("Contract-Bot MVP")
st.caption("Priyanshu Rathee")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "chain" not in st.session_state:
    st.session_state.chain = get_chain()

for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

user_input = st.chat_input("Ask about the contracts…")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    answer, sources = ask(st.session_state.chain, user_input, st.session_state.chat_history)

    st.session_state.chat_history.append(("assistant", answer))
    with st.chat_message("assistant"):
        st.markdown(answer)

        if sources:
            with st.expander("Sources"):
                for doc in sources:
                    src = doc.metadata.get("source", "?")
                    page = doc.metadata.get("page", "?")
                    st.markdown(f"*{src}* – page {page}")