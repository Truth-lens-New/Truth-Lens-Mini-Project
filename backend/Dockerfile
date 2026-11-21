FROM python:3.13-slim

WORKDIR /app

# Install runtime libraries and build only in this layer. Removing the compiler
# before the layer is committed prevents it from inflating the final image.
# CPU-only PyTorch avoids CUDA packages and is installed exactly once.
COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgl1 libglib2.0-0 \
    && pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /root/.cache /var/lib/apt/lists/*

# Copy application
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
