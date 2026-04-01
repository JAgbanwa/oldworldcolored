FROM python:3.11-slim

WORKDIR /app

# System dependencies (OpenCV headless needs libGL-free, but we might need ffmpeg for video)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install PyTorch CPU-only first (much smaller than the default CUDA build)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

# Download model weights at build time so they are baked into the image.
# If the download fails (e.g. network issues in CI), the startup script
# will retry automatically.
RUN python download_models.py || echo "[warn] Model download deferred to startup."

EXPOSE 8000

CMD ["./start.sh"]
