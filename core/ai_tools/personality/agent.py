from __future__ import annotations

from core.ai_tools.ollama import OllamaClient
from .memory.embeddings import get_embedding
from .memory.vector_memory import VectorMemory
from .personas.persona import Persona


class Agent:
    def __init__(self, persona: Persona, memory_path: str):
        self.persona = persona
        self.memory = VectorMemory(index_path=memory_path)
        self.client = OllamaClient()

    def learn(self, text: str) -> None:
        emb = get_embedding(text, self.persona.model)
        self.memory.add(emb, {"text": text})

    def ask(self, query: str, include_memory: bool = True) -> str:
        q_emb = get_embedding(query, self.persona.model)
        context = self.memory.search(q_emb) if include_memory else []
        context_text = "\n\n".join([c.get("text", "") for c in context])
        prompt = f"""You are {self.persona.name}, a {self.persona.style} expert.
Your goals: {', '.join(self.persona.goals)}

{f'Context:\n{context_text}' if context_text else ''}

User: {query}
Respond in your tone.
"""
        response = self.client.generate(prompt, model=self.persona.model)
        return response or ""

    @classmethod
    def load(cls, name: str) -> "Agent":
        persona = Persona.load(name)
        path = f"data/{name}.index"
        return cls(persona, path)
