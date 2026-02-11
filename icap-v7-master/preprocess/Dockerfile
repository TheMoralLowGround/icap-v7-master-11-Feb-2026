FROM aidbdockers/backend-base-python3.10:1

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ONNXTR_CACHE_DIR=/tmp/onnxtr_cache

WORKDIR /app

RUN apt-get update && \
    apt-get install -y poppler-utils && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the necessary directories have the correct permissions
RUN mkdir -p /app/model/onxtr /app/init-scripts /tmp/onnxtr_cache && \
    chown -R 1001:0 /app && \
    chmod -R g=u /app && \
    chmod -R 777 /app/model /tmp/onnxtr_cache && \
    chmod +x /app/init-scripts/*.sh

# Keep as root to access mounted volumes
USER 0
