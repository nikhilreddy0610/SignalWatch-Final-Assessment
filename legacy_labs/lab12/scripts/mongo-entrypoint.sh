#!/usr/bin/env bash
set -Eeuo pipefail

: "${MONGO_ADMIN_USER:?Set MONGO_ADMIN_USER}"
: "${MONGO_ADMIN_PASSWORD:?Set MONGO_ADMIN_PASSWORD}"
: "${APP_READ_USER:?Set APP_READ_USER}"
: "${APP_READ_PASSWORD:?Set APP_READ_PASSWORD}"
: "${APP_WRITE_USER:?Set APP_WRITE_USER}"
: "${APP_WRITE_PASSWORD:?Set APP_WRITE_PASSWORD}"
: "${HR_USER:?Set HR_USER}"
: "${HR_PASSWORD:?Set HR_PASSWORD}"

TLS_DIR=/data/tls
mkdir -p "$TLS_DIR" /data/db

if [[ ! -s "$TLS_DIR/ca.crt" || ! -s "$TLS_DIR/mongodb.pem" || ! -s "$TLS_DIR/client.pem" ]]; then
  openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
    -keyout "$TLS_DIR/ca.key" -out "$TLS_DIR/ca.crt" \
    -subj "/CN=MongoDB-Lab-CA" \
    -addext "basicConstraints=critical,CA:TRUE" >/dev/null 2>&1

  openssl req -new -newkey rsa:2048 -nodes \
    -keyout "$TLS_DIR/server.key" -out "$TLS_DIR/server.csr" \
    -subj "/CN=mongo" >/dev/null 2>&1
  cat > "$TLS_DIR/server.ext" <<'EOF'
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:localhost,DNS:mongo,IP:127.0.0.1
EOF
  openssl x509 -req -days 365 -in "$TLS_DIR/server.csr" \
    -CA "$TLS_DIR/ca.crt" -CAkey "$TLS_DIR/ca.key" -CAcreateserial \
    -out "$TLS_DIR/server.crt" -extfile "$TLS_DIR/server.ext" >/dev/null 2>&1
  cat "$TLS_DIR/server.key" "$TLS_DIR/server.crt" > "$TLS_DIR/mongodb.pem"

  openssl req -new -newkey rsa:2048 -nodes \
    -keyout "$TLS_DIR/client.key" -out "$TLS_DIR/client.csr" \
    -subj "/CN=mongodb-lab-client" >/dev/null 2>&1
  cat > "$TLS_DIR/client.ext" <<'EOF'
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth
EOF
  openssl x509 -req -days 365 -in "$TLS_DIR/client.csr" \
    -CA "$TLS_DIR/ca.crt" -CAkey "$TLS_DIR/ca.key" -CAcreateserial \
    -out "$TLS_DIR/client.crt" -extfile "$TLS_DIR/client.ext" >/dev/null 2>&1
  cat "$TLS_DIR/client.key" "$TLS_DIR/client.crt" > "$TLS_DIR/client.pem"
  chmod 0600 "$TLS_DIR/ca.key" "$TLS_DIR/server.key" "$TLS_DIR/client.key" \
    "$TLS_DIR/mongodb.pem" "$TLS_DIR/client.pem"
  echo "[OK] Generated a lab CA, server certificate, and client certificate."
fi

mongod --bind_ip_all --port 27017 --dbpath /data/db --auth \
  --tlsMode requireTLS \
  --tlsCertificateKeyFile "$TLS_DIR/mongodb.pem" \
  --tlsCAFile "$TLS_DIR/ca.crt" &
MONGOD_PID=$!
trap 'kill -TERM "$MONGOD_PID" 2>/dev/null || true; wait "$MONGOD_PID" || true' TERM INT

MONGO_URI="mongodb://127.0.0.1:27017/?tls=true&tlsCAFile=$TLS_DIR/ca.crt&tlsCertificateKeyFile=$TLS_DIR/client.pem&serverSelectionTimeoutMS=30000"
MONGO_ARGS=(--quiet "$MONGO_URI")

ready=0
for _ in $(seq 1 60); do
  if (:</dev/tcp/127.0.0.1/27017) 2>/dev/null; then
    ready=1
    break
  fi
  if ! kill -0 "$MONGOD_PID" 2>/dev/null; then
    echo "[ERROR] mongod exited before becoming ready." >&2
    wait "$MONGOD_PID"
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  echo "[ERROR] mongod did not become ready within 60 seconds." >&2
  exit 1
fi

if [[ ! -f /data/db/.lab-admin-created ]]; then
  echo "[INFO] Creating the first administrator using MongoDB's localhost exception."
  mongosh "${MONGO_ARGS[@]}" --file /opt/lab/create-admin.js
  touch /data/db/.lab-admin-created
else
  echo "[OK] Existing administrator setup detected."
fi

mongosh "${MONGO_ARGS[@]}" \
  --username "$MONGO_ADMIN_USER" --password "$MONGO_ADMIN_PASSWORD" \
  --authenticationDatabase admin --file /opt/lab/init-users.js
mongosh "${MONGO_ARGS[@]}" \
  --username "$MONGO_ADMIN_USER" --password "$MONGO_ADMIN_PASSWORD" \
  --authenticationDatabase admin --file /opt/lab/seed.js

echo "[OK] MongoDB is running with authentication and TLS required on port 27017."
wait "$MONGOD_PID"
