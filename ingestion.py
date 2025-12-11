"""Ingest PDF and text contracts into a Chroma vector store with rate limiting."""

import glob
import logging
import os
import shutil
import time

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    PDF_GLOB,
    TXT_GLOB,
    INDEX_DIR,
    COLLECTION_NAME,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Batch size for embeddings to avoid rate limits
BATCH_SIZE = 50
BATCH_DELAY_SECONDS = 2


def ingest(pdf_glob: str = PDF_GLOB, txt_glob: str = TXT_GLOB, index_dir: str = INDEX_DIR) -> None:
    """Load PDFs and text files, chunk, embed in batches, and store in Chroma."""
    
    # Clear existing index for fresh start
    if os.path.exists(index_dir):
        logger.info(f"Removing existing index: {index_dir}")
        shutil.rmtree(index_dir)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    )

    docs = []
    
    # Load PDFs
    pdf_files = glob.glob(pdf_glob)
    for pdf in pdf_files:
        try:
            logger.info(f"Processing PDF: {pdf}")
            loaded = PyPDFLoader(pdf).load()
            docs.extend(splitter.split_documents(loaded))
        except Exception as e:
            logger.error(f"Failed to load PDF {pdf}: {e}")
            continue
    
    # Load text files
    txt_files = glob.glob(txt_glob)
    for txt in txt_files:
        try:
            logger.info(f"Processing TXT: {txt}")
            loaded = TextLoader(txt, encoding='utf-8').load()
            docs.extend(splitter.split_documents(loaded))
        except Exception as e:
            logger.error(f"Failed to load TXT {txt}: {e}")
            continue

    total_files = len(pdf_files) + len(txt_files)
    if total_files == 0:
        logger.warning(f"No files found: {pdf_glob} or {txt_glob}")
        return

    if not docs:
        logger.warning("No documents to ingest.")
        return

    total_chunks = len(docs)
    logger.info(f"Loaded {total_files} files, {total_chunks} chunks")
    logger.info(f"Ingesting in batches of {BATCH_SIZE}...")

    # Process in batches to avoid rate limits
    db = None
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE
        
        logger.info(f"  Batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
        
        try:
            if db is None:
                # First batch - create the collection
                db = Chroma.from_documents(
                    batch,
                    embeddings,
                    persist_directory=index_dir,
                    collection_name=COLLECTION_NAME,
                )
            else:
                # Subsequent batches - add to existing collection
                db.add_documents(batch)
            
            # Delay between batches to avoid rate limits
            if i + BATCH_SIZE < total_chunks:
                time.sleep(BATCH_DELAY_SECONDS)
                
        except Exception as e:
            if "429" in str(e) or "RateLimit" in str(e):
                logger.warning(f"Rate limited, waiting 60s...")
                time.sleep(60)
                # Retry this batch
                if db is None:
                    db = Chroma.from_documents(
                        batch,
                        embeddings,
                        persist_directory=index_dir,
                        collection_name=COLLECTION_NAME,
                    )
                else:
                    db.add_documents(batch)
            else:
                raise

    logger.info(f"Vector store created: {index_dir}")
    logger.info(f"Total chunks indexed: {total_chunks}")


if __name__ == "__main__":
    ingest()
