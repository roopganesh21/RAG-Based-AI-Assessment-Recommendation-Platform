# Use a slim Python image to keep the container light
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all your project files into the container
COPY . .

# Hugging Face Spaces uses port 7860 by default
# We use 'main:app' assuming your FastAPI instance is in main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
