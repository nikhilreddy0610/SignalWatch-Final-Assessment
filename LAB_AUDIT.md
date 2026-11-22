# Source audit — uploaded MongoDB Labs 7–18

## Scope and source handling
The uploaded `Archive.zip` contains the Lab 7–18 submission folders and also older Lab 1–6 folders. This assessment assembly preserves Labs 7–18 under `legacy_labs/lab07` through `legacy_labs/lab18`. Local `.env` files, MongoDB keyfiles, private-key files, Python bytecode caches and large backup-dump folders were excluded from the copied source tree. `.env.example` templates and reports are retained where present. The separate final-assessment PDF was not present as a distinct PDF file in the archive; the final-assessment A.1–A.7 instructions were available in the user's message and used as the implementation specification.

## Lab-by-lab review

| Lab | Uploaded work reviewed | Findings and integration decision |
|---|---|---|
| 7 | `cyber-threat-intelligence-labs/app.py`, static dashboard, scripts, README and submission report | SignalWatch's data model and knowledge seed follow the CTI sources/reports/indicators design. Original Lab 7 notes that seeded records are illustrative and feed keyword classification is not analyst-confirmed. RSS feed refresh is not automatically treated as a verified active threat. |
| 8 | Replica-set Compose files, JS initialization/step-down/priority scripts and Python verification scripts | The consolidated MongoDB service runs as a single-node replica set for transaction-ready local operation. The three-member and arbiter/failover demonstrations remain in `legacy_labs/lab08`; they are not all started in the final Compose stack. |
| 9 | Write-concern latency, partition simulation and results CSV | Write concern and consistency/availability/latency trade-offs are captured in RAG knowledge. Original experiment remains preserved; it is not rerun by the chat service. |
| 10 | Bank-transfer and inventory-reservation transaction scripts, runner and Compose | Transaction semantics, rollback and retry guidance are included. The final single-node replica set supports MongoDB transaction semantics; the original transaction benchmarks are preserved, not rerun on every startup. |
| 11 | Sharding cluster Compose, shard-key evaluation, hotspot scripts and report | Shard-key distribution, query targeting and monotonic-key hotspot risks are included in RAG. The full config-server/shard topology is retained as reference code, not launched by the lightweight final stack. |
| 12 | MongoDB security Dockerfiles/Compose, TLS verification, RBAC setup and report | Secret-handling, TLS, least-privilege and view-redaction guidance is included in the assistant knowledge. The final local Compose stack is not yet using the Lab 12 TLS/RBAC deployment; README/report explicitly mark this as production hardening still required. |
| 13 | Docker Compose replica-set deployment, keyfile generation, Kubernetes StatefulSet/headless service, verification notes and report | The final application has one app image, a MongoDB service, persistent storage and health checks. Original Docker/Kubernetes lab implementation remains preserved. Kubernetes deployment is not part of this local Compose run. |
| 14 | Monitoring, backup scheduler, backup/restore verification, benchmark, logs and reports | Health endpoint and basic chat rate limiting are included. Full scheduled backup/restore and metrics dashboard are not automatically executed by the final app; use the preserved Lab 14 scripts for the separate demonstration. |
| 15 | FastAPI multi-tenant API, JWT/RBAC, migration script, tests and benchmark outputs | Per-session chat memory, optional API-key protection and basic per-IP chat rate limiting are included. Full JWT user identities, tenant-specific collection isolation and migration workflow remain preserved in Lab 15 and are not represented as completed in the consolidated app. |
| 16 | FastAPI hybrid service, MongoDB/Cassandra/Neo4j adapters, university model and circuit-breaker service | The original multi-database adapter code is retained in `legacy_labs/lab16`. The final assessment app uses MongoDB as its operational database; Cassandra and Neo4j are not started by the final Compose file to keep the local stack manageable. |
| 17 | Voyage embedding pipeline, MongoDB Atlas Vector Search RAG, five-message conversation memory and FAISS HNSW/IVF benchmark | SignalWatch uses Ollama for local embeddings/chat where installed and MongoDB for knowledge plus conversation memory. It uses last-five-message history. Local MongoDB Community uses API-side cosine retrieval; native Atlas `$vectorSearch` needs Atlas and a matching index. HNSW/IVF benchmark scripts and outputs are preserved, not rerun by the app. |
| 18 | Synthetic threat generator, false-positive detector, MongoDB/Cassandra/Neo4j stores, four benchmark scripts, report and Compose | SignalWatch includes threat lifecycle records and teaches the Lab 18 heuristic false-positive logic. Original 100,000-record synthetic workflow, ten-run median benchmark and multi-database adapters remain preserved. Synthetic labels are not represented as verified real-world threat verdicts. |

## Cross-cutting issues identified

1. Several original labs are separate standalone Compose stacks. Starting all of them together would create duplicate MongoDB services, port conflicts and excessive resource use. The final Compose stack therefore starts one consolidated app image and one MongoDB replica-set service; source folders are included inside the app image for traceability.
2. Lab 17's source uses Voyage AI and MongoDB Atlas Vector Search, while the final request prefers Ollama. The new app uses the existing Ollama service and provides a lexical fallback. Native Atlas vector search is a documented deployment option, not falsely claimed as active in local Community MongoDB.
3. Lab 18 data is synthetic. Its false-positive rules are heuristics, not a production-grade classifier or confirmation of an incident.
4. A local laptop scan is different from threat-feed monitoring. The provided scanner is read-only and checks package inventory/update signals and OSV exact-version matches where supported. It does not perform endpoint detection, full filesystem scanning, kernel/driver auditing or Android/iOS device management.
5. Automated remediation is deliberately not enabled. The assistant provides proposed defensive steps only; a human must verify and execute them through a separately controlled process.

## Offline checks run on the assembled project
- Python source syntax compilation: passed.
- Static structural check for required API routes, frontend presence and all Labs 7–18 folders: passed.
- Secret-file scan of assembled tree (`.env`, `keyfile`, `.pem`, `.key`): no matches.
- Docker image build, Docker Compose startup, MongoDB runtime, Ollama model inference, OSV live lookup and GitHub/Docker Hub publishing: not executed in this environment because Docker/Ollama CLIs are absent and outbound package installation/network access is unavailable.
