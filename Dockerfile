FROM python:3.11-slim

ARG AAROH_AI_TARBALL_URL=https://api.github.com/repos/Pahuja07/Aaroh-AI/tarball/main
ARG AAROH_AI_GITHUB_TOKEN=

WORKDIR /app

# Install system dependencies (build-essential, curl, ca-certificates, libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for better layer caching.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --retries 10 --default-timeout 120 -r requirements.txt

# Copy backend codebase. Render builds this repo with Aaroh-backend as context.
COPY . /app/Aaroh-backend/

# Fetch Aaroh-AI at build time because Render's backend repo context cannot see
# the sibling Aaroh-AI checkout from local development.
RUN set -eux; \
    mkdir -p /app/Aaroh-AI; \
    if [ -n "${AAROH_AI_GITHUB_TOKEN}" ]; then \
        curl -fsSL --retry 5 --retry-delay 2 \
            -H "Authorization: Bearer ${AAROH_AI_GITHUB_TOKEN}" \
            -H "Accept: application/vnd.github+json" \
            "${AAROH_AI_TARBALL_URL}" -o /tmp/aaroh-ai.tar.gz; \
    else \
        curl -fsSL --retry 5 --retry-delay 2 \
            -H "Accept: application/vnd.github+json" \
            "${AAROH_AI_TARBALL_URL}" -o /tmp/aaroh-ai.tar.gz \
        || (echo "Unable to download Aaroh-AI. If the repo is private, set AAROH_AI_GITHUB_TOKEN as a Render Docker build arg with read access." >&2; exit 1); \
    fi; \
    tar -xzf /tmp/aaroh-ai.tar.gz -C /app/Aaroh-AI --strip-components=1; \
    test -d /app/Aaroh-AI/src/aaroh; \
    rm -f /tmp/aaroh-ai.tar.gz

WORKDIR /app/Aaroh-backend

ENV PYTHONPATH=/app/Aaroh-backend:/app/Aaroh-AI:/app/Aaroh-AI/src
ENV AAROH_AI_PATH=/app/Aaroh-AI

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
