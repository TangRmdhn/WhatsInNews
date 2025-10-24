from openai import OpenAI
import streamlit as st
from MyRAG import rangkuman, LLM_chat

st.set_page_config(
    page_title="My baca file",
    page_icon="🤓"
)

st.title("🤓My baca file☝")
st.markdown("Input File (PDF Only)")
uploaded_pdf = st.file_uploader(" ",type="pdf")

if uploaded_pdf:
    rangkum = rangkuman(uploaded_pdf)
    with st.chat_message("assistant"):
        st.markdown(rangkum)
else:
    st.chat_input("Upload File dulu", disabled=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if uploaded_pdf:
    if prompt := st.chat_input("Tanyakan apa saja tentang file"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        response = LLM_chat(prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
