FROM registry.access.redhat.com/ubi8/python-39:1-48

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

USER 0

RUN chmod +x ./init-scripts/*

USER 1001
