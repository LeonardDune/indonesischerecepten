Embedding microservice

This small FastAPI service exposes a POST /embed endpoint that returns embeddings computed by `sentence-transformers`.

Build (use CPU PyTorch wheels):

docker build --build-arg PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu -t embeddings-service:local embeddings_service/

deploy/run:

docker run --rm -p 8000:8000 embeddings-service:local

Environment variables:
- EMBED_MODEL (optional): sentence-transformers model name (default: sentence-transformers/all-mpnet-base-v2)
