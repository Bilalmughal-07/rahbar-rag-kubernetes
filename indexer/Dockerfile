FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DEFAULT_TIMEOUT=300 PIP_RETRIES=10
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade zlib1g \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 indexer
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://pypi.org/simple \
    --timeout 300 --retries 10 -r requirements.txt
RUN pip install --no-cache-dir --index-url https://pypi.org/simple \
    --timeout 300 --retries 10 --no-deps rapidocr-onnxruntime==1.2.3
COPY pipeline ./pipeline
USER 10001
CMD ["python", "-m", "pipeline.run"]
