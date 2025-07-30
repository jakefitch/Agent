#!/usr/bin/env python3
"""Simple CLI demonstrating the personality Agent with persistent memory."""

import argparse
import os
from core.ai_tools.personality import Agent


def main() -> None:
    parser = argparse.ArgumentParser(description="Interact with a personality agent")
    parser.add_argument("--persona", default="blenshaw", help="Persona name from personas.json")
    parser.add_argument("--no-memory", action="store_true", help="Ignore memory when answering")
    args = parser.parse_args()

    os.makedirs("data", exist_ok=True)

    agent = Agent.load(args.persona)
    print(f"Loaded persona: {agent.persona.describe()}")
    print("Type 'teach <text>' to teach, 'ask <question>' to query, or 'quit' to exit")

    while True:
        try:
            inp = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not inp:
            continue
        if inp.lower() in {"quit", "exit"}:
            break
        if inp.startswith("teach "):
            text = inp[6:].strip()
            agent.learn(text)
            agent.memory.save()
            print("[Memory saved]")
            continue
        if inp.startswith("ask "):
            question = inp[4:].strip()
            response = agent.ask(question, include_memory=not args.no_memory)
            print(response)
            continue
        print("Unknown command. Use 'teach', 'ask', or 'quit'.")


if __name__ == "__main__":
    main()

