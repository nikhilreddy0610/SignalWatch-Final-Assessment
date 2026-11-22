# Lab 13.1 - Docker Compose Replica Set

This deployment runs three MongoDB 7.0 members (`mongo1`-`mongo3`) on a
private Compose network. Each member has its own persistent volume. Internal
member authentication uses a generated keyfile in a Docker-managed volume;
the keyfile initializer sets owner `999:999` and mode `0400`. A bootstrap
administrator is generated locally into the ignored `.env`.

## Start

```sh
cd Lab-13.1-Docker
./generate-keyfile.sh
docker compose up -d
docker compose ps
```

Wait until `init-replica-set` exits successfully, then check the members:

```sh
docker compose exec mongo1 mongosh --quiet \
  -u "$(sed -n 's/^MONGO_INITDB_ROOT_USERNAME=//p' .env)" \
  -p "$(sed -n 's/^MONGO_INITDB_ROOT_PASSWORD=//p' .env)" \
  --authenticationDatabase admin \
  --eval 'rs.status().members.map(m => ({name:m.name,stateStr:m.stateStr}))'
```

One node should report `PRIMARY`, and two should report `SECONDARY`. If
restarting the project after data volumes were initialized, the initializer is
idempotent. Local ports are bound only to `127.0.0.1` (27117-27119) to avoid colliding with existing
MongoDB services on the default ports.

## PyMongo and failover tests

Run the PyMongo checks from the Compose network, where the member hostnames
advertised by MongoDB resolve:

```sh
docker compose --profile test run --rm pymongo-test
docker compose --profile test run --rm pymongo-test python failover-test.py
```

The failover test only prints `PASS` after `hello` reports a different writable
primary; it times out as a failure otherwise. This command deliberately steps
down the current primary. To run locally instead, install `requirements.txt`
and use a URI reachable from the host; account for the replica set's advertised
member names.

## Docker Hub demo image

```sh
set -a; . ./.env; set +a
cd ..
docker build -f Lab-13.1-Docker/Dockerfile -t nikhil1386/mongodb-lab13-demo:latest .
docker run --rm \
  --network lab-131-docker_mongo-net \
  -e "MONGODB_URI=mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0&authSource=admin" \
  nikhil1386/mongodb-lab13-demo:latest
```

The image contains the PyMongo verification and failover clients and their dependencies, not
MongoDB credentials, keyfiles, Compose secrets, or the database server. Publish
only after reviewing Docker Hub visibility and logging in interactively.

## Stop

```sh
docker compose down
```

Persistent named volumes are retained. To intentionally erase lab data, use
`docker compose down -v` after confirming the data is disposable.
