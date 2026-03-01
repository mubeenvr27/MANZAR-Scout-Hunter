FROM node:20-bookworm-slim

# 1. Install system tools as root
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv build-essential ca-certificates git tini \
    && npm install -g n8n@latest \
    && rm -rf /var/lib/apt/lists/*

# 2. Create the venv and IMMEDIATELY give ownership to node user
RUN python3 -m venv /opt/venv && chown -R node:node /opt/venv

# 3. Switch to node user for the rest of the setup
USER node
ENV PATH="/opt/venv/bin:$PATH"

# 4. Install libraries inside the venv as the node user
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir google-genai llama-parse requests arxiv

WORKDIR /home/node/manzar-research-scout
EXPOSE 5678
ENTRYPOINT ["tini", "--", "n8n", "start"]