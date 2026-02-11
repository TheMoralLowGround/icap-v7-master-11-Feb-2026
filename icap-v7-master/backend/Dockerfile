FROM aidbdockers/backend-base-python3.10:1

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_OFFLINE=1
ENV HF_DATASETS_OFFLINE=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libreoffice \
    fonts-noto-cjk \
    && \
    # Rebuild the font cache to ensure new fonts are recognized \
    fc-cache -f -v && \
    # Clean up the apt cache to reduce final image size \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip3 install torch==2.7.1+cpu torchvision==0.22.1+cpu torchaudio==2.7.1+cpu --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x ./init-scripts/*
