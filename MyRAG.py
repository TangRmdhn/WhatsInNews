from pypdf import PdfReader
import os
import shutil
from dotenv import load_dotenv
# imports for langchain

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders.telegram import text_to_docs
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from langchain_chroma import Chroma
from uuid import uuid4

from openai import OpenAI

load_dotenv(override=True)
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def bacaPDF(file_bytes):
    """Membaca teks dari file PDF yang diupload."""

    reader = PdfReader(file_bytes)
    full_text = "".join(page.extract_text() for page in reader.pages)
    return full_text

def chunks(teks):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunked = text_splitter.split_text(teks)
    
    docs = text_to_docs(chunked)
    return docs


# VectorDB
def VectorStore(docs):
    db_name = "chroma_langchain_db"

    vector_store = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory=db_name,
    )


    uuids = [str(uuid4()) for _ in range(len(docs))]


    if os.path.exists(db_name):
        vector_store.reset_collection()

    vector_store.add_documents(documents=docs, ids=uuids)

def retrive(user):
    db_name = "MyChromaDB"
    vector_store = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory=db_name,
    )

    results = vector_store.similarity_search(
        user,
        k=10
    )

    full_context = ""
    for res in results:
        full_context += res.page_content

    return full_context

def rangkuman(file_path):
    full_teks = bacaPDF(file_path)
    docs = chunks(full_teks)
    VectorStore(docs)

    MODEL = "gpt-4o-mini"
    openai = OpenAI()
    system_message = """
    Kamu adalah asisten untuk merangkum kesulurhan isi. Buat dalam bentuk paragraf dan berikan poin poin penting yang ada di dalam teks nya. Buat Tulisan jangan terlalu panjang.
"""

    messages = [{"role": "system", "content": system_message}, {"role": "user", "content": full_teks}]
    response = openai.chat.completions.create(model=MODEL, messages=messages)
    
    return response.choices[0].message.content

def LLM_chat(user):
    retrive_context = retrive(user)
    MODEL = "gpt-4o-mini"
    openai = OpenAI()
    
    system_message = f"""
    Kamu adalah asisten chatbot bertugas tanya jawab berdasarkan konteks yang diberikan.
"""

    user_prompt = f"""
    Kamu adalah asisten chatbot bertugas tanya jawab berdasarkan context yang diberikan.
    Jika tidak tahu, bilang "Informasi itu tidak ada di dalam file".

    [KONTEKS]
    {retrive_context}

    [USER]
    {user}
"""

    messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_prompt}]
    response = openai.chat.completions.create(model=MODEL, messages=messages, temperature=0.7)
    
    return response.choices[0].message.content