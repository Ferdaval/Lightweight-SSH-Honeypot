#!/bin/bash
# Quick setup script (US-11)
set -e
echo "[setup] Generating RSA host key..."
mkdir -p keys
ssh-keygen -t rsa -b 4096 -f keys/server.key -N "" -q
echo "[setup] Building Docker image..."
docker-compose build
echo "[setup] Starting honeypot..."
docker-compose up -d
echo "[setup] Done! Honeypot running on port 2222"
echo "[setup] Logs:    ./logs/"
echo "[setup] Reports: ./reports/"
