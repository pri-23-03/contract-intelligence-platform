"""
rag_chat.py
-----------
Builds the Retrieval‑Augmented Generation (RAG) chain and exposes a helper
for asking questions against the contract vector store.

• Loads embeddings and the Chroma vector store.
• Configures an Azure Chat model (o3‑mini by default).
• Wraps both in a ConversationalRetrievalChain.
• Provides `ask()` to run a query with scope guardrails.
"""

# --- Standard library
import os
from typing import List, Tuple

# --- Third‑party
import dotenv                                 # loads .env config
from langchain_openai import (
    AzureChatOpenAI,                          # chat completion model
    AzureOpenAIEmbeddings,                    # embedding model
)
from langchain.chains import ConversationalRetrievalChain  # RAG wrapper
from langchain_community.vectorstores import Chroma        # vector DB

dotenv.load_dotenv()

# LLM guardrail: keeps answers grounded in contract text
SYSTEM_PROMPT = (
    "You are Contract-Bot. Only answer questions that can be answered "
    "using the provided contract excerpts. "
    "If the answer is not in the excerpts, reply: "
    "'I’m sorry, that’s outside the scope of these contracts.'"
)

def get_chain(index_dir: str = "contracts_index") -> ConversationalRetrievalChain:
    """
    Construct and return a ConversationalRetrievalChain that
    1. embeds queries,
    2. retrieves top‑k relevant chunks from Chroma,
    3. feeds them to the Azure Chat model for answer synthesis.
    """
    #  Instantiate embedding client (text‑embedding‑3‑small)
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview"),
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
    )

    # Open the persisted Chroma store and attach the embedding function
    db = Chroma(
        persist_directory=index_dir,
        collection_name="contracts",
        embedding_function=embeddings,
    )

    # Create chat LLM (o3‑mini) 
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "o3-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview"),
        max_completion_tokens=8192,
    )

    # Wrap retriever + LLM into a single RAG chain
    return ConversationalRetrievalChain.from_llm(
        llm,
        db.as_retriever(search_kwargs={"k": 40}),
        return_source_documents=True,
        chain_type="stuff",
    )


def ask(
    chain: ConversationalRetrievalChain,
    question: str,
    chat_history: List[Tuple[str, str]],
):
    """
    Run a single question through the RAG chain, applying the system prompt.
    Returns (answer text, list_of_source_documents).
    """
    # Prefix question with scope guard prompt and invoke chain
    result = chain.invoke(
    {
        "question": f"{SYSTEM_PROMPT}\n\nUser: {question}",
        "chat_history": chat_history,
    }
)
    return result["answer"], result["source_documents"]