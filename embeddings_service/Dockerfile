FROM python:3.11-slim AS builder
ARG PIP_EXTRA_INDEX_URL=
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN if [ -n "$PIP_EXTRA_INDEX_URL" ]; then \
      pip wheel --no-cache-dir --wheel-dir /wheels --extra-index-url "$PIP_EXTRA_INDEX_URL" -r requirements.txt; \
    else \
      pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt; \
    fi
# Copy export script and builder requirements, install heavy build deps, then run export to produce model.onnx
COPY export_to_onnx.py ./export_to_onnx.py
COPY requirements.builder.txt ./requirements.builder.txt
RUN if [ -n "$PIP_EXTRA_INDEX_URL" ]; then \
      pip wheel --no-cache-dir --wheel-dir /wheels --extra-index-url "$PIP_EXTRA_INDEX_URL" -r requirements.builder.txt; \
      pip install --no-cache-dir --extra-index-url "$PIP_EXTRA_INDEX_URL" -r requirements.builder.txt; \
    else \
      pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.builder.txt; \
      pip install --no-cache-dir -r requirements.builder.txt; \
    fi
# Run the export (will create /wheels/model.onnx)
RUN python export_to_onnx.py --model_name "${MODEL_NAME:-sentence-transformers/all-MiniLM-L6-v2}" --output /wheels/model.onnx
# create a small runtime-only wheel set to copy into final image (avoid copying large builder wheels like torch)
RUN mkdir -p /runtime_wheels && \
    for pkg in $(awk -F'==' '/^[^#]/{print $1}' requirements.txt); do \
        ls /wheels/${pkg}* 2>/dev/null && mv /wheels/${pkg}* /runtime_wheels/ 2>/dev/null || true; \
    done && \
    # include onnxruntime and tokenizers wheels
    ls /wheels/onnxruntime* 2>/dev/null && mv /wheels/onnxruntime* /runtime_wheels/ 2>/dev/null || true && \
    ls /wheels/tokenizers* 2>/dev/null && mv /wheels/tokenizers* /runtime_wheels/ 2>/dev/null || true && \
    # copy model files into runtime_wheels for later COPY
    ls /wheels/model*.onnx 2>/dev/null && cp /wheels/model*.onnx /runtime_wheels/ 2>/dev/null || true

FROM python:3.11-slim
WORKDIR /app
# Limit thread parallelism at container level to reduce runtime memory usage
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV OMP_WAIT_POLICY=PASSIVE
COPY --from=builder /runtime_wheels /wheels
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && \
  # Try installing onnxruntime from local wheels, otherwise install from PyPI without deps
  (pip install --no-cache-dir --no-index --find-links /wheels --no-deps onnxruntime || pip install --no-cache-dir --no-deps onnxruntime) && \
  # Try installing tokenizers from local wheels, otherwise from PyPI
  (pip install --no-cache-dir --no-index --find-links /wheels tokenizers || pip install --no-cache-dir tokenizers) && \
  # Try installing runtime requirements from local wheels, otherwise fall back to PyPI
  (pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt || pip install --no-cache-dir -r requirements.txt) && rm -rf /wheels

COPY main.py ./main.py
# copy tokenizer saved by the builder and the exported ONNX model
# copy quantized model (if produced) or fallback to FP32 model
COPY --from=builder /wheels/model-quant.onnx ./model-quant.onnx
COPY --from=builder /wheels/model.onnx ./model.onnx
COPY --from=builder /wheels/tokenizer ./tokenizer
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
# Run a single worker to keep RAM usage predictable
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
