FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV HF_HUB_OFFLINE=1
RUN echo "alias ll='ls -la'" >> ~/.bashrc
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/local_spark/. /app

EXPOSE 5412

CMD ["uvicorn server:app --host 0.0.0.0 --port 5412"]
