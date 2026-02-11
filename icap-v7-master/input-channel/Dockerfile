FROM aidbdockers/backend-base-python3.10:1

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/static /app/media /app/core/migrations && \
    chown -R 1001:0 /app && \
    chmod -R g=u /app

RUN chmod +x ./init-scripts/*
