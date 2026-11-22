#!/bin/sh
set -eu

cd "$(dirname "$0")"
umask 077
mkdir -p secrets

if [ ! -f .env ]; then
  username="labadmin"
  password="$(openssl rand -hex 24)"
  printf 'MONGO_INITDB_ROOT_USERNAME=%s\nMONGO_INITDB_ROOT_PASSWORD=%s\n' \
    "$username" "$password" > .env
  chmod 600 .env
  echo "Created private .env with a randomly generated database password."
else
  echo "Keeping existing .env."
fi

if [ ! -s secrets/keyfile ]; then
  openssl rand -base64 756 | tr -d '\n' > secrets/keyfile
  chmod 400 secrets/keyfile
  echo "Created secrets/keyfile (mode 0400) for Kubernetes."
else
  echo "Keeping existing secrets/keyfile."
fi
