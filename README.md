## Workflow

1. **Prepare & Ingest Contracts**  
   - Drop your contract PDFs into the `data/` folder.  
   - Run `python ingestion.py` to:
     - Load and split each PDF into 500-token chunks.
     - Generate embeddings for each chunk via Azure’s `text-embedding-3-small` model.
     - Persist the vector store in `contracts_index/`.

2. **Build the RAG Chain**  
   - In `rag_chat.py`, load the same embedding model and open the Chroma store.
   - Configure a semantic retriever (`k=20`) to fetch top chunks.
   - Instantiate `AzureChatOpenAI` (o3-mini) with a high `max_completion_tokens` budget.
   - Use `ConversationalRetrievalChain.from_llm(...)` to wire retriever + LLM, with system-prompt guardrails and source-document return.

3. **Run the Streamlit UI**  
   - Launch the app with `streamlit run app.py`.
   - The UI holds a scrolling chat window:
     - User queries are prefixed with a system prompt.
     - The chain retrieves chunks, invokes the LLM, and returns grounded answers with citations.
     - Off-topic questions return a polite “outside scope” message.


4. **Optional Benchmark**  
   - Populate `eval_set.csv` with test questions and answers.
   - Run `python eval.py` to measure accuracy and P95 latency.

## Technologies & Dependencies

### Core Language
- **Python 3.10+**: Primary scripting language used for orchestration, data manipulation, API interaction, and backend logic.

### Web UI
- **Streamlit**: Python-based framework enabling rapid development of interactive web applications, utilized for creating user-friendly interfaces with components like `st.chat_message`, `st.chat_input`, and session state management.
 
### PDF Handling
- **PyPDFLoader (via LangChain)**: Extracts text content from PDFs, converting raw PDF files into structured, textual data.
- **fpdf**: Generates dummy contract PDFs for testing, enabling rapid prototyping and development without dependency on external documents.

### Text Processing and Chunking
- **RecursiveCharacterTextSplitter (LangChain)**: Breaks down extracted PDF text into manageable chunks of approximately 500 tokens, maintaining context through chunk overlaps (100 tokens) to ensure semantic continuity.

### Embeddings & Semantic Search
- **AzureOpenAIEmbeddings (LangChain OpenAI)**: Generates high-dimensional semantic embeddings for text chunks, allowing semantic similarity searches to identify relevant information quickly.
- **ChromaDB**: Local vector database used to store and query embeddings efficiently, facilitating rapid semantic search and retrieval of relevant chunks based on query similarity.

### Language Models & API Interaction
- **AzureChatOpenAI (LangChain OpenAI)**: Interface to Azure’s OpenAI API (specifically o3-mini deployment), facilitating natural language generation tasks, answering queries, and summarizing retrieved chunks based on provided context.

### Environmental Configuration
- **python-dotenv**: Manages secure loading and parsing of environment variables (e.g., API keys, endpoints) from a `.env` file, providing a clean and secure method to handle sensitive configurations.

### Token Management & Cost Estimation
- **tiktoken**: Provides precise token counting for both input and output, aiding in accurate cost estimation and optimization of language model usage.

### Benchmarking & Evaluation
- **CSV & eval.py**: Custom evaluation script running accuracy and latency benchmarks against test questions and expected answers stored in CSV format, enabling objective measurement of model performance.

### Supporting SDK
- **openai**: Python SDK for interaction with Azure OpenAI services, underpinning all API communication required for language generation and embeddings tasks.


## Methods & Architecture

### Step 1: PDF Ingestion  
The ingestion process begins with `ingestion.py`, which leverages `PyPDFLoader` from LangChain to load and extract textual data from PDF contract documents. These raw text documents are then segmented into manageable chunks (approximately 500 tokens each, with a 100-token overlap) by using the `RecursiveCharacterTextSplitter`. This chunking maintains sufficient context across segments, ensuring seamless semantic continuity for subsequent embedding and retrieval.

### Step 2: Embedding Generation  
After text chunks are created, each chunk is transformed into a high-dimensional semantic embedding vector. This embedding generation is performed using `AzureOpenAIEmbeddings` from LangChain OpenAI, specifically utilizing the `text-embedding-3-small` Azure deployment. Embeddings enable the Contract-Bot to quickly and accurately identify relevant contract excerpts by performing semantic similarity searches.

### Step 3: Vector Storage  
Generated embeddings and their associated metadata (such as source PDF and chunk indices) are stored in ChromaDB, a local vector database optimized for fast semantic queries. ChromaDB organizes these embeddings efficiently, allowing for rapid retrieval of relevant information during user queries.

### Step 4: Semantic Retrieval  
When a user submits a query, the retrieval stage is activated. Chroma’s semantic retriever, configured with `k=20`, fetches the top 20 most semantically relevant chunks based on embedding similarity to the user’s question. This retrieval step is pivotal in ensuring that the most pertinent contract information is delivered to the language model for synthesis.

### Step 5: Conversational Retrieval Chain  
Retrieved chunks are passed to the `ConversationalRetrievalChain`, instantiated from LangChain's `from_llm` method. This chain integrates the AzureChatOpenAI language model (specifically the o3-mini deployment), which synthesizes a coherent, contextually accurate response. The model generates answers by leveraging the context provided from relevant chunks, ensuring answers are directly grounded in contract data.

### Step 6: System Prompt & Scope Guard  
To maintain the model’s output within the intended operational scope, each user question is prefixed with a specialized `SYSTEM_PROMPT`. This prompt explicitly instructs the model to only answer questions based on provided contract excerpts. If the semantic retriever returns no relevant chunks, the model defaults to a polite response: "I’m sorry, that’s outside the scope of these contracts."

### Step 7: UI Rendering  
The user-facing interface, implemented via Streamlit (`app.py`), offers a smooth, interactive chat experience. Users can input queries in natural language through a simple chat interface. The Streamlit UI maintains conversation history, displaying clearly formatted answers along with expandable source citations, providing transparency and traceability for each response.

### Step 8: Benchmark Harness  
To evaluate and benchmark the accuracy and performance of the Contract-Bot, the custom evaluation script `eval.py` is employed. This script runs predefined test questions stored in a CSV file (`eval_set.csv`) against expected answers, computing overall accuracy and P95 latency metrics. These benchmarks provide objective measures of reliability and responsiveness, guiding iterative improvements.
