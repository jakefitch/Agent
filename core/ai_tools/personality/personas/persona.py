class Persona:
    def __init__(self, name: str, style: str, goals: list[str], model: str = "llama3:8b"):
        self.name = name
        self.style = style
        self.goals = goals
        self.model = model

    def describe(self) -> str:
        return f"{self.name} speaks in a {self.style} tone. Goals: {', '.join(self.goals)}"

    @classmethod
    def load(cls, name: str):
        import json, os
        path = os.path.join(os.path.dirname(__file__), "personas.json")
        with open(path, "r") as f:
            data = json.load(f)
        p = data.get(name)
        if not p:
            raise ValueError(f"Persona '{name}' not found")
        return cls(name, **p)
