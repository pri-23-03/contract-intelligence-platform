"""Centralized configuration for BillFlow - B2B Billing Contract Intelligence."""

import os
import dotenv

dotenv.load_dotenv()

# Azure OpenAI / Foundry
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-nano")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
)

# Chunking - smaller chunks for better precision
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300
PDF_GLOB = "data/*.pdf"
TXT_GLOB = "data/*.txt"

# Vector store
INDEX_DIR = "contracts_index"
COLLECTION_NAME = "contracts"

# Retrieval - higher k for comparison questions that need multiple docs
RETRIEVER_K = 60

# LLM
MAX_COMPLETION_TOKENS = 8192
