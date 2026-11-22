import unittest

import numpy as np

from app.documents import chunk_text
from benchmark.run_benchmark import recall_percent


class ChunkingTests(unittest.TestCase):
    def test_chunks_respect_size_and_overlap(self):
        words = [f"word{i}" for i in range(230)]
        chunks = chunk_text(" ".join(words))
        self.assertEqual([len(chunk.split()) for chunk in chunks], [100, 100, 70])
        self.assertEqual(chunks[0].split()[-20:], chunks[1].split()[:20])

    def test_invalid_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            chunk_text("text", words_per_chunk=10, overlap=10)


class RecallTests(unittest.TestCase):
    def test_recall_is_top_twenty_overlap_average(self):
        exact = np.arange(40).reshape(2, 20)
        found = exact.copy()
        found[0, 0] = 100
        self.assertEqual(recall_percent(found, exact), 97.5)


if __name__ == "__main__":
    unittest.main()
