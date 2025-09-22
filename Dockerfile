# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
#COPY ./requirements.txt .
RUN pip install --no-cache-dir langchain langchain-openai python-dotenv fpdf2 openai Pillow gradio

# Copy the application source code
COPY ./src ./src

# Expose the port the app runs on
EXPOSE 7860

# Set the server name to allow external connections
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Command to run the application
CMD ["python", "src/app.py"]