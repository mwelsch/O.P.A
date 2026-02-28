FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server/*.py /app/
COPY server/version.json /app/version.json
COPY web-ui /app/web-ui

EXPOSE 8000 28946

CMD ["python", "-u", "main.py"]
