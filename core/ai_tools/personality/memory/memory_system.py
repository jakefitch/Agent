from __future__ import annotations

from typing import Optional

from .vector_memory import VectorMemory
from .embeddings import get_embedding


class MemorySystem:
    def __init__(self, path: str, dim: int = 1536):
        self.vector = VectorMemory(dim=dim, index_path=path)

    def remember(self, text: str, meta: Optional[dict] = None, model: str = "llama3:8b") -> None:
        emb = get_embedding(text, model)
        self.vector.add(emb, meta or {"text": text})

    def recall(self, query: str, k: int = 5, model: str = "llama3:8b"):
        q = get_embedding(query, model)
        return self.vector.search(q, k=k)

    def save(self) -> None:
        self.vector.save()
