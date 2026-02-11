FROM registry.access.redhat.com/ubi8/python-39:1-48

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

USER 0

COPY . .

RUN chown -R 1001:0 ./

RUN chmod +x keygrid_main
RUN chmod +x single_column_extractor
RUN chmod +x ./init-scripts/*

RUN mkdir temp

RUN chgrp -R 0 /app/temp && \
    chmod -R g=u /app/temp

USER 1001
