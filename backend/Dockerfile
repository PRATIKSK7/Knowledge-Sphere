FROM python:3.12-slim

WORKDIR /app

# Install system dependencies needed for parsing documents, OCR, build tools, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    poppler-utils \
    tesseract-ocr \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# spaCy model download removed — spaCy is not used in this project

# Create upload directory
RUN mkdir -p /app/uploads

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
