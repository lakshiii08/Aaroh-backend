FROM python:3.11-slim

ARG AAROH_AI_REPO_URL=https://github.com/Pahuja07/Aaroh-AI.git
ARG AAROH_AI_REF=main

WORKDIR /app

# Install system dependencies (build-essential, curl, git, libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for better layer caching.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase. Render builds this repo with Aaroh-backend as context.
COPY . /app/Aaroh-backend/

# Fetch Aaroh-AI at build time because Render's backend repo context cannot see
# the sibling Aaroh-AI checkout from local development.
RUN set -eux; \
    git clone --depth 1 --branch "${AAROH_AI_REF}" "${AAROH_AI_REPO_URL}" /app/Aaroh-AI \
    || (git clone "${AAROH_AI_REPO_URL}" /app/Aaroh-AI && cd /app/Aaroh-AI && git checkout "${AAROH_AI_REF}"); \
    rm -rf /app/Aaroh-AI/.git

WORKDIR /app/Aaroh-backend

ENV PYTHONPATH=/app/Aaroh-backend:/app/Aaroh-AI:/app/Aaroh-AI/src
ENV AAROH_AI_PATH=/app/Aaroh-AI

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
