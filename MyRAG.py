import os
import requests
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders.telegram import text_to_docs
from langchain_chroma import Chroma
from uuid import uuid4

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
MODEL = 'gpt-4o-mini'
openai = OpenAI()

headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    """
    A utility class to represent a Website that we have scraped, now with links
    """

    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"


link_system_prompt = "You are provided with a list of links found on a webpage. \
You are able to decide which of the links would be most relevant to include about the news headline, \
such as links to an next page, or a source person page.\n"
link_system_prompt += "You should respond in JSON as in this example:"
link_system_prompt += """
{
    "links": [
        {"type": "next page", "url": "https://full.url/goes/here/about/page=num"},
        {"type": "another page", "url": "https://another.full.url/careers"}
    ]
}
"""

def get_links_user_prompt(website):
    user_prompt = f"This is the headline {website.title} - "
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web links for a news about the headline, respond with the full https URL in JSON format. \
Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

def get_links(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(website)}
      ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    return json.loads(result)

def get_all_details(url):
    result = "Landing page:\n"
    result += Website(url).get_contents()
    links = get_links(url)
    for link in links["links"]:
        result += f"\n\n{link['type']}\n"
        result += Website(link["url"]).get_contents()
    return result

system_prompt_fulltext = """
Tujuan Anda adalah menghasilkan teks berita yang SEMPURNA untuk membuat vektor embedding.

[Instruksi Wajib]:
1. Baca judul sebagai referensi utama.
2. Hasil akhir harus HANYA berisi konten berita inti yang relevan.
3. Keluarkan hasilnya dalam format teks biasa tanpa format tambahan.
"""

def get_fulltext_user_prompt(url):
    headline = Website(url).title
    user_prompt = f"Headline Berita : {headline}\n"
    user_prompt += f"Berikut adalah isi halaman berita dan halaman relevan lainnya; gunakan informasi ini untuk membangun teks berita lengkap dalam teks biasa.\n"
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:5000]
    return user_prompt

def create_full_text(url):
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt_fulltext},
            {"role": "user", "content": get_fulltext_user_prompt(url)}
          ],
    )
    result = response.choices[0].message.content
    return result

def chunks(url):
    teks = create_full_text(url)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunked = text_splitter.split_text(teks)
    
    docs = text_to_docs(chunked)
    return docs

def VectorStore(url):
    docs = chunks(url)
    db_name = "MyChromaDB"

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
        k=5
    )

    full_context = ""
    for res in results:
        full_context += res.page_content

    return full_context

def stream_response_generator(response_stream):
    """
    Generator function to yield content chunks from the OpenAI stream.
    """
    for chunk in response_stream:
    
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

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
    

    response_stream = openai.chat.completions.create(
        model=MODEL, 
        messages=messages, 
        temperature=0.7,
        stream=True
    )
    
    return stream_response_generator(response_stream)

system_prompt_summary = "Anda adalah asisten yang menganalisis konten beberapa halaman relevan dari situs web berita dan membuat kesimpulan serta inti berita untuk calon pembaca." \
"Tanggapi dalam format Markdown. Sertakan detail jika Anda memiliki informasinya."

def get_summary_user_prompt(url):
    headline = Website(url).title
    user_prompt = f"Headline berita : {headline}\n"
    user_prompt += f"Berikut adalah konten halaman berita dan halaman relevan lainnya; gunakan informasi ini untuk membangun kesimpulan dan inti berita dalam markdown..\n"
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:5_000]
    return user_prompt

def create_summary(url):

    response_stream = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt_summary},
            {"role": "user", "content": get_summary_user_prompt(url)}
          ],
        stream=True
    )

    return stream_response_generator(response_stream)

