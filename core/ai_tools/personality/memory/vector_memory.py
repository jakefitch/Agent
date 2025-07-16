import os
import pickle
from typing import Any, List

import numpy as np

try:
    import faiss  # type: ignore
except ImportError:  # fallback simple index
    faiss = None


class VectorMemory:
    def __init__(self, dim: int = 1536, index_path: str | None = None):
        self.dim = dim
        self.index_path = index_path
        self.metadata: List[Any] = []
        if faiss:
            self.index = faiss.IndexFlatL2(dim)
        else:
            self.index = []  # type: ignore
        if index_path and os.path.exists(index_path):
            self.load(index_path)

    def add(self, embedding: List[float], meta: Any) -> None:
        if faiss:
            self.index.add(np.array([embedding], dtype=np.float32))
        else:
            self.index.append(np.array(embedding, dtype=np.float32))  # type: ignore
        self.metadata.append(meta)

    def search(self, embedding: List[float], k: int = 5) -> List[Any]:
        if not self.metadata:
            return []
        query = np.array([embedding], dtype=np.float32)
        if faiss:
            D, I = self.index.search(query, k)
            return [self.metadata[i] for i in I[0] if i < len(self.metadata)]
        else:
            # naive search
            vectors = np.vstack(self.index)
            distances = np.linalg.norm(vectors - query, axis=1)
            idx = np.argsort(distances)[:k]
            return [self.metadata[i] for i in idx]

    def save(self) -> None:
        if not self.index_path:
            raise ValueError("No index path defined.")
        if faiss:
            faiss.write_index(self.index, self.index_path)
        else:
            with open(self.index_path, "wb") as f:
                pickle.dump(self.index, f)
        with open(self.index_path + ".meta", "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self, path: str) -> None:
        if faiss and os.path.exists(path):
            self.index = faiss.read_index(path)
        elif os.path.exists(path):
            with open(path, "rb") as f:
                self.index = pickle.load(f)
        if os.path.exists(path + ".meta"):
            with open(path + ".meta", "rb") as f:
                self.metadata = pickle.load(f)
