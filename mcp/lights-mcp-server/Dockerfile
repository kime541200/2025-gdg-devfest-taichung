FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 2828
CMD ["python", "-m", "src.server", "--host", "0.0.0.0", "--port", "2828"]
