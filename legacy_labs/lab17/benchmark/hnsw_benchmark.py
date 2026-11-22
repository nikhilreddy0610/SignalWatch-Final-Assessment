from benchmark.settings import TOP_K


def build_hnsw(faiss, vectors):
    index = faiss.IndexHNSWFlat(vectors.shape[1], 32, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = 80
    index.hnsw.efSearch = 64
    index.add(vectors)
    return index


def search_hnsw(index, queries):
    return index.search(queries, TOP_K)[1]
