# Multi-stage Dockerfile for Dog Nose Embedder gRPC Server

FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime system dependencies (if any)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY generate_proto.py .

# Copy proto file and generate Python code
COPY src/presentation/proto/nose_embedder.proto ./src/presentation/proto/
RUN python generate_proto.py

# Download ONNX model from NCP Object Storage (if credentials provided)
# ARGs can be passed during build: --build-arg NCP_ACCESS_KEY=xxx
ARG NCP_ACCESS_KEY
ARG NCP_SECRET_KEY
ARG NCP_ENDPOINT=https://kr.object.ncloudstorage.com
ARG NCP_REGION=kr-standard
ARG NCP_BUCKET_NAME
ARG NCP_MODEL_KEY=models/embedder_model.onnx

# Download model script - runs only if NCP credentials are provided
COPY download_model.py .
RUN if [ -n "$NCP_ACCESS_KEY" ] && [ -n "$NCP_SECRET_KEY" ] && [ -n "$NCP_BUCKET_NAME" ]; then \
        echo "Downloading model from NCP Object Storage..."; \
        python download_model.py \
            --access-key "$NCP_ACCESS_KEY" \
            --secret-key "$NCP_SECRET_KEY" \
            --endpoint "$NCP_ENDPOINT" \
            --region "$NCP_REGION" \
            --bucket "$NCP_BUCKET_NAME" \
            --key "$NCP_MODEL_KEY" \
            --output embedder_model.onnx; \
        echo "Model downloaded from NCP Object Storage"; \
    else \
        echo "NCP credentials not provided, skipping download"; \
    fi

# Create non-root user for security
RUN useradd -m -u 1000 grpcuser && \
    chown -R grpcuser:grpcuser /app

USER grpcuser

# Expose gRPC port
EXPOSE 50052

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/embedder_model.onnx

# Run the application
CMD ["python", "-m", "src.main"]
