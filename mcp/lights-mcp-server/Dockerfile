FROM python:3.12-slim

WORKDIR /app

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     git \
#     curl \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 2828
CMD ["python", "-m", "src.server", "--host", "0.0.0.0", "--port", "2828"]
