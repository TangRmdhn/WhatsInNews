import streamlit as st
from MyRAG import create_summary, LLM_chat

st.set_page_config(
    page_title="My Baca Berita",
    page_icon="🤓",
    layout="wide"
)

st.title("🤔 Rangkum & Chat Berita")
st.write("Masukkan URL berita di kiri untuk membuat rangkuman. Setelah diproses, Anda bisa bertanya tentang berita tersebut di chatbot sebelah kanan.")

# --- State Management ---
# Kita perlu simpan beberapa hal di session_state biar nggak hilang
# 'summary' = Teks rangkuman
# 'rag_ready' = Flag (True/False) penanda VectorDB sudah dibuat apa belum
# 'messages' = History chat

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "rag_ready" not in st.session_state:
    st.session_state.rag_ready = False

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Layout Aplikasi ---
col1, col2 = st.columns([1.5, 1])

# --- KOLOM 1: Input & Rangkuman ---
with col1:
    st.header("Rangkuman Berita")
    
    url = st.text_input("Masukan link berita:", placeholder="https://url-berita-anda.com/...")

    if st.button("Proses Berita"):
        if url:
            with st.spinner("Mengambil data, membuat rangkuman, dan membangun database RAG... Ini mungkin butuh waktu..."):
                try:
                    # Fungsi ini akan (1) membuat rangkuman dan (2) membangun VectorDB
                    summary = create_summary(url) 
                    st.session_state.summary = summary
                    st.session_state.rag_ready = True # Set flag RAG siap!
                    st.session_state.messages = [] # Kosongkan chat history lama
                    st.success("Rangkuman dan RAG siap!")
                except Exception as e:
                    st.error(f"Gagal memproses URL: {e}")
                    st.session_state.rag_ready = False
        else:
            st.warning("Silakan masukkan URL terlebih dahulu.")
    
    # Tampilkan rangkuman jika sudah ada
    if st.session_state.summary:
        summary_text = st.session_state.summary
        
        # Cek jika string di-wrap ` ```markdown ... ``` `
        if summary_text.strip().startswith("```markdown"):
            # Hapus baris pertama (```markdown) dan baris terakhir (```)
            summary_text = summary_text.strip()[10:-3].strip() 
            
        # Cek jika string di-wrap ` ``` ... ``` ` (tanpa 'markdown')
        elif summary_text.strip().startswith("```"):
            # Hapus baris pertama (```) dan baris terakhir (```)
            summary_text = summary_text.strip()[3:-3].strip()
        # --- BATAS BAGIAN PENTING ---

        st.markdown(summary_text)

# --- KOLOM 2: Chatbot RAG ---
with col2:
    st.header("Tanya Jawab (RAG)")

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Cek apakah RAG sudah siap
    if not st.session_state.rag_ready:
        st.info("Silakan proses URL berita di sebelah kiri terlebih dahulu untuk mengaktifkan chat.")
        disabled_chat = True
    else:
        disabled_chat = False

    # React to user input
    if prompt := st.chat_input("Tanyakan apa saja tentang berita:", disabled=disabled_chat):
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get assistant response
        with st.spinner("Mencari jawaban..."):
            response = LLM_chat(prompt) # Memanggil fungsi RAG
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})