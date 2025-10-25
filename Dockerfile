# Multi-stage Dockerfile for Dog Nose Embedder gRPC Server

FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

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
    apt-get install -y --no-install-recommends libgomp1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Generate protobuf files during build
RUN python -m grpc_tools.protoc \
    -I./src/presentation/proto \
    --python_out=. \
    --grpc_python_out=. \
    ./src/presentation/proto/nose_embedder.proto && \
    echo "Protobuf files generated successfully"

# Copy ONNX model file (included in Docker image)
COPY embedder_model.onnx ./embedder_model.onnx

# Create model cache directory
RUN mkdir -p /tmp/models && chmod 755 /tmp/models

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
