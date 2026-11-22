"""Exact cosine top-k search used as the benchmark recall reference."""

import numpy as np


def exact_top_k(vectors: np.ndarray, queries: np.ndarray, k: int) -> np.ndarray:
    scores = queries @ vectors.T
    return np.argpartition(scores, -k, axis=1)[:, -k:]
