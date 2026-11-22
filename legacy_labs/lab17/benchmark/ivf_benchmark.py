from benchmark.settings import TOP_K


def build_ivf(faiss, vectors):
    quantizer = faiss.IndexFlatIP(vectors.shape[1])
    index = faiss.IndexIVFFlat(
        quantizer, vectors.shape[1], 100, faiss.METRIC_INNER_PRODUCT
    )
    index.train(vectors)
    index.add(vectors)
    index.nprobe = 10
    return index


def search_ivf(index, queries):
    return index.search(queries, TOP_K)[1]
