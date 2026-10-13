FROM python:3.11-slim

WORKDIR /app

# Install system curl for healthcheck & libpq dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY main.py .
COPY .env .

EXPOSE 8092

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8092/health || exit 1

CMD ["python", "main.py"]
