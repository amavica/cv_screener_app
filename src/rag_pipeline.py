# src/rag_pipeline.py

import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableMap
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Constants
VECTOR_STORE_PATH = "vector_store"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_rag_chain():
    """
    Creates and returns a RAG chain for querying the vector store.
    This chain will be used by the frontend UI.
    """
    # 1. Load the persisted vector store
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_PATH,
        embedding_function=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    )
    retriever = vector_store.as_retriever()

    # 2. Initialize the LLM
    llm = ChatOpenAI(
        model="google/gemini-2.0-flash-exp:free",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    # 3. Define the Prompt Template
    template = """
    You are an expert HR assistant. Your task is to answer questions about a collection of candidate CVs.
    Use only the following context to answer the question. Do not use any of your own knowledge.
    If the context does not contain the answer, state that you cannot find the information in the provided CVs.
    Be concise and professional in your response.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    prompt = ChatPromptTemplate.from_template(template)

    # 4. Helper function to format retrieved documents
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # 5. Construct the RAG Chain
    rag_chain_with_sources = RunnableMap({
        "context": retriever, 
        "question": RunnablePassthrough()
    }) | {
        "answer": (
            RunnablePassthrough.assign(context=lambda x: format_docs(x["context"]))

| prompt
| llm
| StrOutputParser()
        ),
        "sources": lambda x: [os.path.basename(doc.metadata.get('source', 'Unknown')) for doc in x["context"]]
    }

    return rag_chain_with_sources