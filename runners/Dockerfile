# Change from 1.76.1 to latest
FROM n8nio/runners:latest

USER root
ENV UV_HTTP_TIMEOUT=300

# Install MANZAR research libraries
RUN cd /opt/runners/task-runner-python && \
    uv pip install --python .venv/bin/python \
    google-generativeai llama-parse arxiv requests

USER runner