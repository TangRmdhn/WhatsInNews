import streamlit as st
from MyRAG import create_summary, LLM_chat, VectorStore

st.set_page_config(
    page_title="Whats In News",
    page_icon="📰",
    layout="wide"
)

st.title("📰Rangkum & Chat Berita")

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "rag_ready" not in st.session_state:
    st.session_state.rag_ready = False

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages_rangkum = False

col1, col2 = st.columns([1.5, 1])

with col1:
    st.header("🗞️ Rangkuman Berita")
    
    url = st.text_input("Masukan link berita:", placeholder="https://url-berita-anda.com/...")

    if st.button("Proses Berita"):
        if url:
            with st.spinner("Sedang mengakses berita"):
                try:
                
                    summary_stream_generator = create_summary(url) 
                    
                    st.session_state.messages = []
                    st.session_state.rag_ready = False
                    
                
                
                    full_summary = st.write_stream(summary_stream_generator)

                
                    st.session_state.summary = full_summary
                    st.session_state.rag_ready = True
                    VectorStore(url)
                    
                except Exception as e:
                    st.error(f"Gagal memproses URL: {e}")
                    st.session_state.rag_ready = False
        else:
            st.warning("Silakan masukkan URL terlebih dahulu.")
    

    if st.session_state.summary and st.session_state.messages_rangkum:
        summary_text = st.session_state.summary
        
    
        if summary_text.strip().startswith("```markdown"):
        
            summary_text = summary_text.strip()[10:-3].strip() 
            
    
        elif summary_text.strip().startswith("```"):
        
            summary_text = summary_text.strip()[3:-3].strip()
    

        st.markdown(summary_text)

with col2:
    st.header("💬 Bot Tanya Jawab")


    if not st.session_state.rag_ready:
        disabled_chat = True
    else:
        disabled_chat = False
        st.session_state.messages_rangkum = True

    chat_history_container = st.container(height=500, border=True)


    with chat_history_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


    if prompt := st.chat_input("Tanyakan apa saja tentang berita:", disabled=disabled_chat):
        
    
        st.session_state.messages.append({"role": "user", "content": prompt})
        
    
        with chat_history_container: 
            with st.chat_message("user"):
                st.markdown(prompt)

    
        stream_response = LLM_chat(prompt) 
        
    
        with chat_history_container:
            with st.chat_message("assistant"):
                full_response = st.write_stream(stream_response)
            
    
        st.session_state.messages.append({"role": "assistant", "content": full_response})