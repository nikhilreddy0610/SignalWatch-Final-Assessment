# MongoDB Lab 17 — RAG and Vector Search Index Comparison

A demonstrable threat-intelligence RAG CLI backed by MongoDB Atlas Vector Search, Voyage AI embeddings, OpenAI-compatible generation, and MongoDB conversation history. The benchmark separately compares local FAISS HNSW and IVF indexes with exact cosine search.

## Features

- Five concise threat-intelligence sources, split into word windows of up to 100 words with 20-word overlap.
- Voyage AI `voyage-3-lite` embeddings (512 dimensions) stored alongside `text` and `source`.
- Atlas `$vectorSearch` retrieves the three nearest chunks.
- Last five conversation messages are read from MongoDB and user/assistant turns are persisted.
- Reproducible 5,000-document, 384-dimensional FAISS benchmark, 100 queries, exact Top-20 recall, CSV and graph.
- Docker CLI image and separate benchmark command.

## Technologies and structure

Python 3.12+, MongoDB Atlas, PyMongo, Voyage AI, OpenAI-compatible chat completions, FAISS, NumPy, Matplotlib, ReportLab, Docker.

```text
app/                 RAG, embedding, MongoDB and CLI code
benchmark/           Corpus generator and FAISS/exact benchmarks
reports/              Generated submission report and graph
Dockerfile            CLI container
docker-compose.yml    Local interactive RAG service
```

## Setup

1. Install Python 3.12+ and create an environment: `python3 -m venv .venv && source .venv/bin/activate`.
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`; set `MONGO_URI`, `VOYAGE_API_KEY`, and `OPENAI_API_KEY`. The LLM endpoint/model may be changed with `OPENAI_BASE_URL` and `LLM_MODEL`. Keep `.env` local.
4. Ensure the Atlas database user and network access list permit the connection. The app creates its chunk and conversation collections as needed and requests creation of the vector index; allow Atlas time to finish building it.

The Atlas vector field uses Voyage `voyage-3-lite` at 512 dimensions, cosine similarity, and a `source` filter field. Atlas Vector Search index configuration does not expose a choice between HNSW and IVF; the `$vectorSearch` stage uses `numCandidates` for approximate-search work. This project does not claim that an IVF Atlas index was created. HNSW and IVF measurements below are local FAISS experiments.

## Lab 17.1: RAG demonstration

```bash
python -m app.main
```

Enter questions about the seed sources (for example, “What should responders do after a ransomware incident?”). Type `exit` to stop. The first run embeds and upserts the sample chunks, and requests Atlas index creation. Conversation records have `user_id`, UTC `timestamp`, `role`, and `content`.

To run in Docker, copy `.env.example` to `.env`, fill in credentials, and use:

```bash
docker compose up --build
```

## Lab 17.2: local HNSW vs IVF benchmark

```bash
python -m benchmark.run_benchmark
```

The generator creates 5,000 topic-structured sample records and normalized 384-dimensional synthetic vectors using a fixed seed. One hundred noisy sample vectors are used as queries. Flat exact cosine Top-20 is the recall reference. HNSW uses `M=32`, `efConstruction=80`, `efSearch=64`; IVF uses `nlist=100`, `nprobe=10`, and flat inner-product lists. Build time includes index construction/training and addition; latency is the mean over individual queries. Run on the same host for meaningful comparisons. Results are hardware- and library-version-dependent.

The CSV and graph are written to `reports/comparison.csv` and `reports/latency_recall.png` (with benchmark data retained under `benchmark/results/`). If `MONGO_URI` is set, the benchmark also writes corpus documents and embeddings to `lab17.benchmark_vectors`; without it, benchmark execution remains local and explicitly reports that storage was skipped.

## Docker

Build and run locally:

```bash
docker build -t mongo-lab17-rag:latest .
docker run --rm -it --env-file .env mongo-lab17-rag:latest
```

To run the benchmark in the built image:

```bash
docker run --rm --env-file .env \
  -v "$PWD/reports:/app/reports" \
  -v "$PWD/benchmark/results:/app/benchmark/results" \
  --entrypoint python mongo-lab17-rag:latest -m benchmark.run_benchmark
```

Published Docker Hub repository: <https://hub.docker.com/r/nikhil1386/mongo-lab17-rag>

Pull and run the published image after creating `.env`:

```bash
docker pull nikhil1386/mongo-lab17-rag:latest
docker run --rm -it --env-file .env nikhil1386/mongo-lab17-rag:latest
```

The image was pushed after a successful local build and container smoke test. Keep credentials in `.env`; they are not included in the image.

## Report

Run `python -m benchmark.run_benchmark` and then `python -m reports.generate_report` to create `reports/Lab17_Report.pdf` with the measured table, chart, student details, and verified Docker Hub link.
