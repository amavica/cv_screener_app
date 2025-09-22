# src/app.py

import gradio as gr
import os
from rag_pipeline import get_rag_chain

# --- 1. Initialize the RAG Chain ---
# This is done once when the application starts.
print("Initializing the RAG chain...")
try:
    rag_chain = get_rag_chain()
    print("RAG chain initialized successfully.")
except Exception as e:
    print(f"Error initializing RAG chain: {e}")
    # If the chain fails to load, we'll display an error in the UI.
    rag_chain = None

# --- 2. Define the Chatbot's Response Logic ---
def chat_response(message, history):
    """
    Handles the chat interaction. Invokes the RAG pipeline and formats the response.
    """
    if rag_chain is None:
        return "Error: The RAG chain could not be initialized. Please check the vector store and API keys."

    print(f"Received message: {message}")
    
    # Invoke the RAG chain with the user's message
    response_dict = rag_chain.invoke(message)
    answer = response_dict.get('answer', "Sorry, I couldn't generate an answer.")
    
    # Process and format the source documents for display
    sources = sorted(list(set(response_dict.get('sources',)))) # Get unique sources
    
    if sources:
        # Create a formatted string for the sources
        source_str = "\n\n*Sources:* " + ", ".join(sources)
        return answer + source_str
    else:
        return answer

# --- 3. Instantiate the Gradio UI ---
# The 'gradio' command will automatically find and launch this interface.
iface = gr.ChatInterface(
    fn=chat_response,
    title="AI-Powered CV Screener",
    description="Ask questions about the candidate CVs. The system will retrieve relevant information and generate an answer.",
    examples=["Who has experience with Python?", "Which candidate graduated from UPC?", "Summarize the profile of Jane Doe."],
    cache_examples=False # Caching can be problematic with dynamic backends
)

# The if __name__ == "__main__": block is no longer needed for launching,
# but can be kept if you ever want to run the script directly with python.
if __name__ == "__main__":
    # This line is now handled by the CMD in the Dockerfile
    iface.launch(server_name="0.0.0.0", server_port=7860)
    print("Application ready. The Gradio CLI will launch the interface.")