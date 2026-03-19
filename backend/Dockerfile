FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including libgl1 for OpenCV)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch CPU


# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application
COPY . .

# Run the application (--reload for dev hot-reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
