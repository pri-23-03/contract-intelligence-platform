"""
ingestion.py
------------
Converts raw PDF contracts into a Chroma vector store.

• Loads PDFs with PyPDFLoader.
• Splits text into overlapping chunks for semantic integrity.
• Generates embeddings via Azure OpenAI.
• Persists vectors + metadata locally for fast retrieval.
"""

# --- Standard library
import glob, os

# --- Third‑party
import dotenv                      # .env loader for API keys & endpoints
from langchain_community.document_loaders import PyPDFLoader  # PDF → text
from langchain.text_splitter import RecursiveCharacterTextSplitter  # chunking
from langchain_openai import AzureOpenAIEmbeddings            # Azure embeddings
from langchain_community.vectorstores import Chroma           # local vector DB

dotenv.load_dotenv()

def ingest(pdf_glob="data/*.pdf", index_dir="contracts_index"):
    """
    Ingest all PDFs matching *pdf_glob*,
    embed their text, and store vectors under *index_dir*.
    """

    # Configure the chunking strategy (2 000‑token chunks, 500‑token overlap)
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)

    # Instantiate Azure embedding client (text‑embedding‑3‑small)
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview"),
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
    )

    # Load and split every PDF in *data/* into text chunks
    docs = []
    for pdf in glob.glob(pdf_glob):
        # Append all chunks from this PDF to our master list
        docs += splitter.split_documents(PyPDFLoader(pdf).load())

    #  put embeddings + metadata into a local Chroma index
    Chroma.from_documents(
        docs,
        embeddings,
        persist_directory=index_dir,
        collection_name="contracts",
    ).persist()

# build the vector store 

if __name__ == "__main__":
    ingest()