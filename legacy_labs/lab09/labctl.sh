#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

usage() {
  echo "Usage: $0 {up|status|benchmark|partition|down}"
}

wait_for_ping() {
  local attempt
  for attempt in $(seq 1 60); do
    if docker compose exec -T mongo1 mongosh --quiet --eval 'db.adminCommand({ping: 1}).ok' 2>/dev/null | grep -q '^1$'; then
      return 0
    fi
    sleep 2
  done
  echo "MongoDB did not become ready within 120 seconds." >&2
  return 1
}

initialize_replicaset() {
  docker compose exec -T mongo1 mongosh --quiet --eval '
    try {
      rs.status();
      print("Replica set rs0 is already initialized.");
    } catch (error) {
      print("Initializing replica set rs0.");
      rs.initiate({
        _id: "rs0",
        members: [
          { _id: 0, host: "mongo1:27017", priority: 2 },
          { _id: 1, host: "mongo2:27017" },
          { _id: 2, host: "mongo3:27017" }
        ],
        settings: { electionTimeoutMillis: 10000 }
      });
    }
  '

  local attempt
  for attempt in $(seq 1 60); do
    if docker compose exec -T mongo1 mongosh --quiet --eval 'db.hello().isWritablePrimary' 2>/dev/null | grep -q '^true$'; then
      echo "Replica set is ready; mongo1 is primary."
      return 0
    fi
    sleep 2
  done
  echo "Replica set did not elect mongo1 as primary within 120 seconds." >&2
  return 1
}

case "${1:-}" in
  up)
    docker compose up -d mongo1 mongo2 mongo3
    wait_for_ping
    initialize_replicaset
    ;;
  status)
    docker compose exec -T mongo1 mongosh --quiet --eval \
      'rs.status().members.forEach(member => print(`${member.name} - ${member.stateStr} - health=${member.health}`))'
    ;;
  benchmark)
    docker compose run --rm --no-deps lab
    ;;
  partition)
    bash ./lab_02_simulate_partition.sh
    ;;
  down)
    docker compose down
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
