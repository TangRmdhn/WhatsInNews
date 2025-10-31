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

# --- Layout Aplikasi ---
col1, col2 = st.columns([1.5, 1])

# --- KOLOM 1: Input & Rangkuman (Tidak Berubah) ---
with col1:
    st.header("🗞️ Rangkuman Berita")
    
    url = st.text_input("Masukan link berita:", placeholder="https://url-berita-anda.com/...")

    if st.button("Proses Berita"):
        if url:
            with st.spinner("Sedang mengakses berita"):
                try:
                    # 1. create_summary sekarang akan menjalankan VectorStore() dan mengembalikan stream.
                    summary_stream_generator = create_summary(url) 
                    
                    st.session_state.messages = [] # Kosongkan chat history lama
                    st.session_state.rag_ready = False # Set RAG sementara False sampai stream selesai
                    
                    # 2. Gunakan st.write_stream() untuk menampilkan stream dan menangkap teks lengkapnya
                    # Karena st.write_stream menampilkan outputnya sendiri, kita bisa langsung tangkap hasilnya.
                    full_summary = st.write_stream(summary_stream_generator)

                    # 3. Simpan hasil akhir
                    st.session_state.summary = full_summary # Simpan teks lengkap (berisi Markdown)
                    st.session_state.rag_ready = True # Set flag RAG siap!
                    VectorStore(url)
                    
                except Exception as e:
                    st.error(f"Gagal memproses URL: {e}")
                    st.session_state.rag_ready = False
        else:
            st.warning("Silakan masukkan URL terlebih dahulu.")
    
    # Tampilkan rangkuman jika sudah ada
    if st.session_state.summary and st.session_state.messages_rangkum:
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

# --- KOLOM 2: Chat Bot (Di-update menggunakan st.container) ---
with col2:
    st.header("💬 Bot Tanya Jawab")

    # Cek apakah RAG sudah siap
    if not st.session_state.rag_ready:
        disabled_chat = True
    else:
        disabled_chat = False
        st.session_state.messages_rangkum = True

    chat_history_container = st.container(height=500, border=True) # Tambahkan height untuk membatasi tinggi dan membuatnya scrollable

    # Display chat messages from history di dalam container
    with chat_history_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 2. Reaksi ke input user (tetap di luar container agar 'nempel' di bawah container)
    if prompt := st.chat_input("Tanyakan apa saja tentang berita:", disabled=disabled_chat):
        
        # 3. Tampilkan pesan user dan tambahkan ke history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Tampilkan pesan user di container chat history
        with chat_history_container: 
            with st.chat_message("user"):
                st.markdown(prompt)

        # 4. Dapatkan objek stream dari MyRAG
        stream_response = LLM_chat(prompt) 
        
        # 5. Tampilkan asisten dengan streaming dan simpan respons lengkap
        with chat_history_container: # Pastikan respons asisten juga masuk ke container
            with st.chat_message("assistant"):
                full_response = st.write_stream(stream_response)
            
        # 6. Tambahkan respons lengkap ke chat history (di state)
        st.session_state.messages.append({"role": "assistant", "content": full_response})