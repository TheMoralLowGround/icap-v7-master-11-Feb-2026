FROM aidbdockers/backend-base-python3.10:1

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Make init scripts executable
RUN mkdir -p init-scripts && \
    chmod +x init-scripts/*.sh

USER 0
