#!/bin/bash
# Generate a self-signed TLS certificate for localhost / custom domain
# Usage: ./generate_certs.sh [domain]
# Default domain: localhost

DOMAIN="${1:-localhost}"
mkdir -p certs

openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -nodes \
  -subj "/CN=${DOMAIN}/O=CSE722 WebAuthn Demo/C=BD" \
  -addext "subjectAltName=DNS:${DOMAIN},DNS:localhost,IP:127.0.0.1"

echo "[+] Certificate generated: certs/cert.pem  certs/key.pem"
echo "[+] Domain: ${DOMAIN}"
