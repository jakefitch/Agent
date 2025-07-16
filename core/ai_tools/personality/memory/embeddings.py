from hashlib import md5
from typing import List

from core.ai_tools.ollama import OllamaClient


def get_embedding(text: str, model: str = "llama3:8b") -> List[float]:
    """Return a deterministic mock embedding for the given text."""
    client = OllamaClient()
    # Placeholder: in real use, call an embedding model here
    _ = client  # suppress unused warning
    h = md5(text.encode()).hexdigest()
    return [float(int(h[i:i+4], 16) % 1000) / 1000 for i in range(0, 32, 4)]
