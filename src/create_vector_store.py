# src/create_vector_store.py

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableMap
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Constants for file paths
CV_DIRECTORY = "cvs_generated"
VECTOR_STORE_PATH = "vector_store"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def create_vector_store():
    """
    Loads PDFs, splits them into chunks, creates embeddings,
    and stores them in a persistent ChromaDB vector store.
    This is a one-time setup process.
    """
    print("--- Starting Vector Store Creation ---")
    
    # 1. Load Documents
    print(f"Loading PDF documents from '{CV_DIRECTORY}'...")
    loader = DirectoryLoader(CV_DIRECTORY, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    if not documents:
        print("No PDF documents found. Please run the generation script first.")
        return
    print(f"Loaded {len(documents)} documents.")

    # 2. Split Text into Chunks
    print("Splitting documents into smaller chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    # 3. Create Embeddings
    print(f"Loading embedding model: '{EMBEDDING_MODEL_NAME}'...")
    # This model runs locally on your CPU
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # 4. Create and Persist Vector Store
    print(f"Creating and persisting vector store at '{VECTOR_STORE_PATH}'...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_STORE_PATH
    )
    print("--- Vector Store Creation Complete ---")

# --- Main Execution Block ---
if __name__ == "__main__":
    # This allows the script to be run directly to perform the data ingestion.
    create_vector_store()