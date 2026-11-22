# MongoDB Replica Set Labs 8.1 and 8.2

Each activity has a standalone Python script and a MongoDB shell (`.js`) file.
The base lab uses three data-bearing members. The 8.1 try-it-yourself activity
uses two data-bearing members and one arbiter, which is the three-vote topology
that demonstrates an odd number of voters without storing a third data copy.

## Requirements

- Docker Desktop with Docker Compose
- Python 3.9 or later
- `python -m pip install pymongo`

Run commands from this directory. The base lab uses host ports 27217-27219 to avoid clashing with the other
MongoDB lab services already using ports 27017-27019. The replica set advertises
`host.docker.internal`, which Docker Desktop resolves for containers and the
host machine.

## Activity 8.1: Three data-bearing members

```sh
docker compose up -d
docker compose exec -T mongo1 mongosh --quiet --norc --file /dev/stdin < activity-8-1/replica_set.js
python3 activity-8-1/verify_replication.py
```

The Python script inserts a document with majority write concern, reports
member roles and health, then reads the document directly from both secondaries.

## Activity 8.1: Try it yourself (arbiter)

This is a separate replica set using ports 27117-27119. It is intentionally
two data-bearing members plus one arbiter: adding an arbiter to the three-data
member base lab would result in four voters, not an odd number.

```sh
docker compose -f activity-8-1-try-it-yourself/docker-compose.yml up -d
docker compose -f activity-8-1-try-it-yourself/docker-compose.yml exec -T data1 mongosh --quiet --norc --file /dev/stdin < activity-8-1-try-it-yourself/replica_set_with_arbiter.js
python3 activity-8-1-try-it-yourself/verify_arbiter_replication.py
```

The arbiter votes in elections but does not store application data or replicate
the oplog. It can help two data-bearing members retain a voting majority if one
data member is unavailable, but it does not provide another recoverable data
copy and cannot serve reads or writes.

## Activity 8.2: Failover observer

Keep the base replica set from Activity 8.1 running.

```sh
python3 activity-8-2/observe_failover.py
```

In another terminal, identify the primary using `rs.status()` and run the
step-down script against that member. Replace `mongo1` below with the Compose
service for the member reported as PRIMARY:

```sh
docker compose exec -T mongo1 mongosh --quiet --norc --file /dev/stdin < activity-8-2/step_down.js
```

MongoDB may close the shell connection as the primary steps down. That is
expected; the observer reports the election gap and the next primary.

## Activity 8.2: Try it yourself (priority)

```sh
docker compose exec -T mongo1 mongosh --quiet --norc --file /dev/stdin < activity-8-2-try-it-yourself/set_priorities.js
python3 activity-8-2-try-it-yourself/observe_priority_election.py
```

Member `mongo2` receives priority 3, `mongo1` priority 2, and `mongo3` priority
1. Once the higher-priority `mongo2` is primary, the predicted successor after
it steps down is `mongo1` (assuming all members are healthy and caught up).
Run the MongoDB script on the current primary (replace `mongo1` in the command
above if necessary), then step down the primary service in the same way as
Activity 8.2. Follow the observer output to verify the prediction.
Priority biases an election; it is not an absolute guarantee under unhealthy or
lagging-member conditions.

## Clean up

```sh
docker compose down
docker compose -f activity-8-1-try-it-yourself/docker-compose.yml down
```

Add `-v` to either command only if you also intend to remove that lab's
persistent database volumes.
