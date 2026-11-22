# MongoDB Sharding Labs 11.1 and 11.2

This submission contains a runnable MongoDB 7.0 sharded-cluster demonstration
and solutions for the two Chapter 11 activities. It uses two single-node shard
replica sets and one single-node config-server replica set for a compact local
demo. This topology is for coursework, not production.

**Student:** K J NIKHIL REDDY  
**USN:** 24BTRCL091

## Run with Docker Compose

Requirements: Docker with the Compose plugin.

```sh
docker compose up -d config shard1 shard2 mongos
docker compose run --rm initialize
docker compose --profile tools run --rm lab evaluate
docker compose --profile tools run --rm lab hotspot
```

`hotspot` inserts 10,000 documents into each collection, so allow a little time
for MongoDB to initialize and finish the insert. It can be run again; the demo
collections are dropped and rebuilt on each run.

To stop the cluster:

```sh
docker compose down
```

To remove the persisted demo data as well:

```sh
docker compose down -v
```

Docker assigns an available host port for mongos to avoid collisions. Find it
with `docker compose port mongos 27017`; connect to `mongodb://localhost:<port>`.
The lab runner uses the internal Compose network and does not depend on this
host port.

The submission PDF is [submission-report.pdf](./submission-report.pdf). To
regenerate it, install the report-only dependency and run:

```sh
python3 -m pip install -r requirements-report.txt
python3 scripts/generate_report.py
```

## Lab 11.1 — Evaluate shard key choices

Run `docker compose --profile tools run --rm lab evaluate` for the printed
decision matrix.

| Candidate | Cardinality | Distribution | Query targeting | Hotspot risk | Verdict |
|---|---|---|---|---|---|
| `order_id` | Very high, normally one per order | Even when generated randomly; potentially skewed if sequential | Excellent for order-ID lookup; customer/date queries scatter | Depends on ID generation; sequential range keys are risky | Good only if order-ID lookups dominate |
| `customer_id` | High if the customer base is large | Can be skewed by customers with unusually many orders | Excellent for retrieving a customer's orders | A very active customer remains on one shard | Good when customer locality matters most |
| `order_date` | High over time | Recent inserts cluster at the high end of a ranged key | Good for date ranges; customer queries scatter | High for an insert-heavy ascending key | Avoid as the sole key for write-heavy orders |
| `customer_id` hashed | High, inherited from customer IDs | Usually balances distinct customer values across shards | Equality lookups by customer target a shard; ranges scatter | Low for distinct-customer writes, but hashing cannot split one hot customer's orders | Recommended among these candidates for customer-centric reads |

### Recommendation and caveats

Use `{customer_id: "hashed"}` if customer order history is the dominant query
and write pattern. It combines equality-query targeting with a broadly even
distribution of distinct customers. Hashing does not guarantee equal document
counts when order volume per customer is highly skewed: all orders for a
particular customer still map to that customer's hashed key. It also removes
ordered range locality. If date-range reads dominate, or a few customers
generate most writes, measure a representative workload and evaluate a
compound or alternative key instead.

### Resharding in MongoDB 5.0+

Resharding changes the shard key of an existing collection online. From
`mongos`, the core operation is:

```javascript
db.adminCommand({
  reshardCollection: "shop.orders",
  key: { customer_id: "hashed" }
})
```

Typical procedure:

1. Check server-version compatibility, unique-index constraints, duplicate
   `_id` values, collection features, cluster health, and available resources.
2. Ensure no index builds are in progress and disable the balancer.
3. Start `reshardCollection` through `mongos`.
4. Monitor the operation through `admin`'s `$currentOp` output.
5. After it completes, verify the key, chunk placement, data, and application
   query plans, then re-enable the balancer.

Resharding copies data to recipient shards and catches up concurrent writes.
Applications should tolerate a brief write-blocking critical section and
increased latency. The operation is write- and resource-intensive; MongoDB
recommends free storage on each recipient of at least
`2 * (collection storage + index size) / shard count`, plus CPU below 80% and
I/O capacity below 50%. Only one collection resharding/move/unshard/rewrite
operation can run at a time. Unique indexes must satisfy shard-key uniqueness
rules; duplicate `_id` values can cause failure. Queryable-encryption
collections are unsupported. Some collection DDL operations are unavailable
while resharding; `addShard`, `removeShard`, and `dropDatabase` on the affected
database wait until it finishes. Check the documentation for the exact MongoDB
version and workload before using resharding in production.

Reference: [MongoDB Manual — Reshard a Collection](https://www.mongodb.com/docs/manual/core/sharding-reshard-a-collection/).

## Lab 11.2 — Detecting a shard-key hotspot

The demo creates:

- `lab11.hotspot_data`, sharded by ascending `{ts: 1}`.
- `lab11.even_data`, sharded by `{user_id: "hashed"}` with two initial chunks.

Both collections receive 10,000 documents with the same timestamps. `collStats`
prints each shard's document count and data size. The range-sharded collection
starts with its timestamp range on one shard, so the increasing writes target
that shard. Pre-splitting the hashed key creates chunks that can be placed on
both shards, so the second collection should be substantially more balanced.
Exact counts may vary with server version and chunk placement.

The script also prints `explain()` winning plans:

- The same `ts` date-range filter targets the timestamp-sharded collection
  according to the timestamp chunk ranges.
- That filter scatters on the hashed-`user_id` collection because `ts` is not
  its shard key.
- A range predicate on the hashed `user_id` key does not provide ordered
  range targeting and is expected to scatter.

Monotonic keys are not universally wrong: ranged shard keys can be appropriate
when range queries are central and the write rate/partitioning strategy avoids
a single active upper-bound chunk, or when writes are not the bottleneck.
Consider compound keys, zones, or a different key only after measuring the
actual workload.

## Docker Hub submission

The submission repository is
[`nikhil1386/mongodb-sharding-lab11`](https://hub.docker.com/r/nikhil1386/mongodb-sharding-lab11).
The `1.0` image is published and the Compose `lab` service pulls it from Docker Hub.
To rebuild and publish an updated image:

```sh
docker login
docker build -t nikhil1386/mongodb-sharding-lab11:1.0 .
docker push nikhil1386/mongodb-sharding-lab11:1.0
```

The MongoDB services use the official `mongo:7.0` image.
