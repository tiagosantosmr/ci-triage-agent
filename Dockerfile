FROM python:3.11-slim

# git: clones the target repo for retrieval and sandboxed verification.
# gh CLI: reads PR/CI state and pushes fixes/comments.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY agent/ agent/
COPY eval/ eval/
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python", "-m", "agent.cli"]

