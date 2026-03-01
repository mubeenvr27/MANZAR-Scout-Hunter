FROM n8nio/runners:latest

USER root

# Install MANZAR research libraries using the built-in 'uv' tool
# This puts them exactly where the sidecar runner can see them
RUN cd /opt/runners/task-runner-python && \
    uv pip install --python .venv/bin/python \
    google-generativeai \
    llama-parse \
    arxiv \
    requests

USER runner