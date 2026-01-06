# Use Python 3.11 slim image (stable and commonly available)
### Builder stage: build wheels for all requirements (keeps final image small)
FROM python:3.11-slim AS builder
ARG PIP_EXTRA_INDEX_URL=
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels
# Copy both pinned and base requirements into the builder context
COPY backend/requirements.pinned.txt ./requirements.pinned.txt
COPY backend/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
# Build wheels for all requirements; allow passing extra index-url for e.g. PyTorch CPU wheels
RUN if [ -n "$PIP_EXTRA_INDEX_URL" ]; then \
      pip wheel --no-cache-dir --wheel-dir /wheels --extra-index-url "$PIP_EXTRA_INDEX_URL" -r requirements.pinned.txt; \
    else \
      pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.pinned.txt; \
    fi

### Runtime stage: install only the built wheels
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY backend/requirements.txt ./requirements.txt
# Install from wheels and remove the wheel cache in the same layer to avoid leaving large files
RUN python -m pip install --upgrade pip && \
  pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt && \
  rm -rf /wheels

# Copy backend source
COPY backend/ ./backend/
WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Use shell form so $PORT is expanded by the shell at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
