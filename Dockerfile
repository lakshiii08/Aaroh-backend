FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential, curl, libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for better layer caching.
COPY Aaroh-backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase and the nested Aaroh-AI core package.
COPY Aaroh-backend/ /app/Aaroh-backend/
COPY Aaroh-AI/Aaroh-AI/ /app/Aaroh-AI/

WORKDIR /app/Aaroh-backend

ENV PYTHONPATH=/app/Aaroh-backend:/app/Aaroh-AI:/app/Aaroh-AI/src
ENV AAROH_AI_PATH=/app/Aaroh-AI

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
