"""RAG chain for querying B2B billing service agreements with professional formatting."""

import logging
from typing import List, Tuple

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    INDEX_DIR,
    COLLECTION_NAME,
    RETRIEVER_K,
    MAX_COMPLETION_TOKENS,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are BillFlow Assistant, an expert analyst for B2B billing service agreements.

## Your Role
You help billing operations teams analyze their client contract portfolio, including:
- Revenue share rates, transaction fees, and platform fees
- SLA commitments (billing accuracy, platform uptime, support response times)
- Payment terms and remittance schedules
- Contract values (monthly, annual, total)
- Client tiers (Enterprise, Business, Standard, Starter)
- Compliance requirements (PCI-DSS, SOC 2)

## Response Format Guidelines
When generating reports or answering questions:

1. **For lists of clients/contracts**: Use a markdown table with relevant columns
2. **For single lookups**: Give a direct, concise answer
3. **For comparisons**: Use a table comparing the key metrics
4. **For compliance/SLA reports**: Structure with headers and bullet points
5. **For financial summaries**: Include totals and averages where relevant

## Formatting Rules
- Use **bold** for key values and client names
- Use tables for any data with 3+ items
- Include a brief "Summary" or "Key Findings" section for reports
- Round currency to nearest dollar, percentages to 2 decimals
- Always cite the contract number (BSA-2024-XXXXX) when referencing specific agreements

## Example Table Format
| Client | Monthly Revenue | Billing Model | SLA |
|--------|----------------|---------------|-----|
| **Clearwave Internet** | $771,664 | Revenue Share (3.5%) | 99.9% |

## Contract Data Available
{context}

## Question
{question}

Respond with well-formatted, professional analysis suitable for executive review."""


def format_docs(docs):
    """Format retrieved documents into a single string."""
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get('source', 'unknown').replace('data/', '').replace('.txt', '').replace('_', ' ').title()
        formatted.append(f"[Source: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)


def get_chain(index_dir: str = INDEX_DIR):
    """Build and return the RAG chain using LCEL."""
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    )

    try:
        db = Chroma(
            persist_directory=index_dir,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )
    except Exception as e:
        logger.error(f"Failed to open vector store: {e}")
        raise

    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": RETRIEVER_K, "fetch_k": RETRIEVER_K * 2}
    )

    llm = AzureChatOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
        api_version=AZURE_OPENAI_API_VERSION,
        max_completion_tokens=MAX_COMPLETION_TOKENS,
    )

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    # Build LCEL chain
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


def _convert_chat_history(chat_history: List[Tuple[str, str]]) -> list:
    """Convert (role, message) tuples to LangChain message objects."""
    messages = []
    for role, content in chat_history:
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def ask(chain_tuple, question: str, chat_history: List[Tuple[str, str]]):
    """Run a question through the RAG chain. Returns (answer, sources)."""
    chain, retriever = chain_tuple
    
    try:
        # Get sources first
        sources = retriever.invoke(question)
        
        # Get answer
        answer = chain.invoke(question)
        
        return answer, sources
    except Exception as e:
        logger.error(f"Chain error: {e}")
        raise
