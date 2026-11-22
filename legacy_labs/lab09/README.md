# MongoDB Lab 9: Write Concern and Network Partitions

This project contains runnable demonstrations for Labs 9.1 and 9.2 using a local three-member MongoDB 7 replica set. Docker Compose keeps the database and benchmark client on the same network.

## Requirements

- Docker Desktop or Docker Engine with the Compose plugin
- Bash

## Start the replica set

```sh
./labctl.sh up
./labctl.sh status
```

The setup uses three voting, data-bearing members on a private Compose network (no host ports are published). `mongo1` has higher election priority so the scripts can target a stable primary. The replica set is initialized automatically and its data persists in named Docker volumes.

## Lab 9.1: Measure write concern latency

```sh
./labctl.sh benchmark
```

The benchmark inserts 1,000 individual documents for each of six configurations: `w:1`, `w:majority`, and all members, each with `j:false` and `j:true`. It prints total elapsed time, average latency per insert, P50, and P99, and writes the same comparison to `results/write_concern_results.csv`.

MongoDB's `w` option does not accept the literal value `"all"`. For this three-member replica set, `w:3` is used to require acknowledgment from all three data-bearing members. `w:majority` requires two of the three. `j:true` additionally asks MongoDB to wait for journal persistence; it is a separate durability setting from replication acknowledgment.

| Write concern | Meaning in this lab |
|---|---|
| `w:1` | Primary acknowledgment |
| `w:majority` | Acknowledgment from at least two of three members |
| `w:3` | Acknowledgment from all three members (the lab's equivalent of “all”) |

### Results and interpretation

Measured in one local Docker run (1,000 individual inserts per configuration):

| Configuration | Total (s) | Average (ms/write) | P50 (ms) | P99 (ms) |
|---|---:|---:|---:|---:|
| `w:1, j:false` | 1.054 | 1.053 | 0.625 | 7.282 |
| `w:1, j:true` | 11.261 | 11.258 | 2.030 | 32.336 |
| `w:majority, j:false` | 12.177 | 12.173 | 6.774 | 68.531 |
| `w:majority, j:true` | 9.382 | 9.378 | 4.658 | 45.005 |
| `w:3, j:false` | 7.741 | 7.738 | 2.937 | 43.571 |
| `w:3, j:true` | 14.820 | 14.813 | 5.569 | 72.678 |

`w:1, j:false` was fastest in this run because the primary did not wait for replication or journal persistence. The stronger replication concerns took longer overall, consistent with waiting for member acknowledgments. `w:majority, j:true` happened to measure faster than `w:majority, j:false`, while `w:1, j:true` had a high average despite a much lower median; this shows how outliers and scheduling noise affect a single run. Journaling can add disk-related latency, but the differences are not strictly monotonic here. Repeat the benchmark and compare medians before drawing conclusions about small differences. The complete measured table is also saved to `results/write_concern_results.csv`.

## Lab 9.2: Simulate a network partition

With the replica set healthy, run:

```sh
./labctl.sh partition
```

The script temporarily disconnects only the `mongo2` container from this Compose project's network, probes `w:1` and `w:majority` writes directly against the primary, prints replica-set status every five seconds for 30 seconds, reconnects `mongo2`, and waits for it to return as a secondary. The script restores the network on interruption or error.

Expected observation: with one member isolated, the primary and the other secondary still form a majority. Both `w:1` and `w:majority` writes should be acknowledged, while the isolated member will be marked unavailable from the primary's view. The member should rejoin and catch up after reconnection. These observations can vary with startup and election timing; record the actual output.

In the verified run using the published Docker image, both writes were acknowledged (about 17 ms for `w:1` and 74 ms for `w:majority`); `mongo2` showed `(not reachable/healthy)` while disconnected, and returned as `SECONDARY` after its network was restored.

For a deeper quorum-loss experiment, disconnect both secondaries from the network and watch the primary's election-timeout behavior. A primary that loses its majority eventually steps down; therefore `w:1` is not guaranteed to remain available indefinitely, and `w:majority` cannot be acknowledged without a quorum. This project does not automate that more disruptive second phase.

## Docker image and submission

The client image is published at [Docker Hub](https://hub.docker.com/r/nikhil1386/mongodb-lab9). Compose runs this published image for both demonstrations:

```sh
docker pull nikhil1386/mongodb-lab9:latest
```

The submission PDF is `submission_report.pdf`. It includes the Docker Hub URL, the measured benchmark table, and the partition results.

To rebuild after changing the client code and publish an updated image:

```sh
docker build -t nikhil1386/mongodb-lab9:latest .
docker push nikhil1386/mongodb-lab9:latest
```

Set `DOCKERHUB_IMAGE=your-username/mongodb-lab9:latest` to use a different image repository. Do not commit Docker credentials.

Stop the replica set (retains data volumes):

```sh
./labctl.sh down
```
