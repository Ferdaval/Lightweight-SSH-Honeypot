FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev libssl-dev libcairo2 libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run as non-root user (NFR-4)
RUN useradd -m -s /bin/false honeypot
RUN mkdir -p /app/logs /app/reports /app/keys && chown -R honeypot:honeypot /app

COPY . .
USER honeypot

# Healthcheck — confirms port is listening (US-11)
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import socket; s=socket.create_connection(('localhost',2222),2); s.close()" || exit 1

EXPOSE 2222
CMD ["python", "main.py"]
