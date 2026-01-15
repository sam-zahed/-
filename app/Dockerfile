FROM python:3.11-slim
WORKDIR /code

# Suppress NNPACK warnings (fixes "Could not initialize NNPACK! Reason: Unsupported hardware")
ENV NNPACK_MAX_THREADS=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    cmake \
    g++ \
    ffmpeg \
    espeak-ng \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# Install additional packages
RUN pip install "git+https://github.com/ultralytics/CLIP.git" 2>/dev/null || true
RUN pip install deep-translator

# Copy application code
COPY ./app /code/app

# Download models (optional - can be done at runtime)
RUN python /code/app/download_models.py || echo "Models will be downloaded at runtime"

# Copy client files
COPY ./client /code/client

# Create data directories
RUN mkdir -p /code/app/data/faces \
    /code/app/data/rooms \
    /code/app/data/zones \
    /code/app/data/environments \
    /code/app/data/learning

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
