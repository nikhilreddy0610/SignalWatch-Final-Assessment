#!/usr/bin/env bash
set -euo pipefail

wait_for_ping() {
  local host="$1"
  local attempt
  for attempt in $(seq 1 60); do
    if mongosh --host "$host" --quiet --eval 'if (!db.adminCommand({ ping: 1 }).ok) quit(1)' >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  printf 'MongoDB endpoint %s did not become available\n' "$host" >&2
  exit 1
}

initialize_replica_set() {
  local host="$1"
  local replica_set="$2"
  local options="$3"
  wait_for_ping "$host"
  mongosh --host "$host" --quiet --eval \
    "try { rs.status(); } catch (e) { rs.initiate({_id: '${replica_set}', ${options}members: [{_id: 0, host: '${host}'}]}); }"

  local attempt
  for attempt in $(seq 1 60); do
    if mongosh --host "$host" --quiet --eval 'if (!db.hello().isWritablePrimary) quit(1)' >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  printf 'Replica set %s did not elect a primary\n' "$replica_set" >&2
  exit 1
}

initialize_replica_set config:27019 cfgRS 'configsvr: true, '
initialize_replica_set shard1:27018 shard1RS ''
initialize_replica_set shard2:27018 shard2RS ''
wait_for_ping mongos:27017

mongosh --host mongos:27017 --quiet --eval '
  const existing = db.adminCommand({listShards: 1}).shards.map(shard => shard._id);
  for (const [name, address] of [
    ["shard1RS", "shard1RS/shard1:27018"],
    ["shard2RS", "shard2RS/shard2:27018"]
  ]) {
    if (!existing.includes(name)) {
      const result = sh.addShard(address);
      if (!result.ok) throw new Error(JSON.stringify(result));
    }
  }
  const result = sh.enableSharding("lab11");
  if (!result.ok) throw new Error(JSON.stringify(result));
'

printf 'MongoDB sharded cluster is initialized.\n'
