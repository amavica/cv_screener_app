# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# 1. Install dependencies
# This layer is only rebuilt when requirements.txt changes
RUN pip install --no-cache-dir langchain \
langchain_openai \
langchain_core \
langchain-huggingface \
langchain_community \
langchain-text-splitters \
langchain-chroma \
python-dotenv \
fpdf2 \
openai \
Pillow \
gradio \
sentence-transformers \
pypdf 

# 2. Copy the rest of the application source code
# This is a separate layer, so changes to code won't trigger a re-install of packages
COPY ./src ./src

# --- Configuration for Gradio ---
# Expose the port the app runs on
EXPOSE 7860

# Set environment variables for the Gradio server
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=7860

# Command to run the application using the Gradio CLI for hot-reloading
CMD ["gradio", "src/app.py"]