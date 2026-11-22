#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

container_id="$(docker compose ps -q mongo2)"
if [[ -z "$container_id" ]]; then
  echo "mongo2 is not running. Start the replica set with ./labctl.sh up first." >&2
  exit 1
fi

network="$(docker inspect --format '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}' "$container_id")"
if [[ -z "$network" ]]; then
  echo "Could not determine the Compose network for mongo2." >&2
  exit 1
fi

disconnected=0
restore_network() {
  if [[ "$disconnected" == "1" ]]; then
    echo "Restoring mongo2 network connection..."
    docker network connect --alias mongo2 "$network" "$container_id"
    disconnected=0
  fi
}
trap restore_network EXIT INT TERM

show_status() {
  docker compose exec -T mongo1 mongosh --quiet --eval \
    'rs.status().members.forEach(member => print(`${member.name} - ${member.stateStr} - health=${member.health}`))'
}

echo "Baseline replica set state:"
show_status
echo
echo "Disconnecting mongo2 from Compose network '$network'."
docker network disconnect "$network" "$container_id"
disconnected=1

echo "Checking writes with the primary and one secondary still connected:"
docker compose run --rm --no-deps \
  -e REPLICA_SET_URI='mongodb://mongo1:27017/?directConnection=true&serverSelectionTimeoutMS=5000' \
  lab /app/lab_02_write_probe.py

echo
echo "Monitoring replica-set status for 30 seconds:"
for elapsed in 0 5 10 15 20 25 30; do
  echo "--- ${elapsed}s ---"
  show_status
  if [[ "$elapsed" != "30" ]]; then
    sleep 5
  fi
done

restore_network
trap - EXIT INT TERM

echo
echo "Waiting up to 60 seconds for mongo2 to rejoin..."
rejoined=0
for attempt in $(seq 1 12); do
  if docker compose exec -T mongo1 mongosh --quiet --eval \
    'rs.status().members.some(member => member.name === "mongo2:27017" && member.stateStr === "SECONDARY")' 2>/dev/null \
    | grep -q '^true$'; then
    rejoined=1
    break
  fi
  sleep 5
done
show_status
if [[ "$rejoined" != "1" ]]; then
  echo "mongo2 did not rejoin as SECONDARY within 60 seconds." >&2
  exit 1
fi
echo
echo "Partition simulation complete. With one of three members isolated, the primary and remaining secondary can still form a majority."
