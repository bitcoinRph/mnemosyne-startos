# syntax=docker/dockerfile:1
# Build context is the repo root: docker buildx build -f deploy/startos/Dockerfile .
FROM python:3.12-slim AS build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

WORKDIR /src
# setup.py reads the version from mnemosyne/__init__.py, so the package source
# must be present for the install to resolve metadata.
COPY pyproject.toml setup.py README.md ./
COPY mnemosyne ./mnemosyne
COPY deploy/startos/server ./deploy/startos/server
RUN pip install ".[mcp,embeddings,sync,media]" ./deploy/startos/server

# Bake the embedding model through Mnemosyne's own loader so the cache layout
# is exactly what it looks up at runtime. Scratch data dirs keep the build from
# creating state that would otherwise ship in the image.
ENV MNEMOSYNE_FASTEMBED_CACHE_DIR=/opt/mnemosyne/fastembed
RUN MNEMOSYNE_DATA_DIR=/tmp/build-data HERMES_HOME=/tmp/build-home \
    python - <<'PY'
from mnemosyne.core import embeddings

model = embeddings._get_model()
assert model is not None, "embedding model did not load"
vectors = embeddings.embed(["warm-up"])
assert vectors is not None and len(vectors) == 1, "embedding produced no vector"
print("baked", embeddings._DEFAULT_MODEL, "dim", len(vectors[0]))
PY

FROM python:3.12-slim

COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/mnemosyne/fastembed /opt/mnemosyne/fastembed

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    MNEMOSYNE_DATA_DIR=/data/mnemosyne \
    MNEMOSYNE_HOME=/data/home \
    HERMES_HOME=/data/home/hermes \
    MNEMOSYNE_SHARED_DB_PATH=/data/mnemosyne/shared/mnemosyne.db \
    MNEMOSYNE_BACKUP_DIR=/data/backups \
    MNEMOSYNE_BLOB_DIR=/data/mnemosyne/blobs \
    MNEMOSYNE_FASTEMBED_CACHE_DIR=/opt/mnemosyne/fastembed \
    HF_HUB_OFFLINE=1

EXPOSE 8080
ENTRYPOINT ["mnemosyne-startos-server"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
