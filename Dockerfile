# Dockerfile

# Python 3.11 slim — smaller image, faster build
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /ford-ai

# Install system dependencies required by faiss-cpu
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker layer caching means
# dependencies only reinstall when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformer model at build time
# so the container starts instantly without a runtime download
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the project
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]