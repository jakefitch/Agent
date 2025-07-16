#!/usr/bin/env python3
"""
Simple script to list available Ollama models.
"""

from ollama import OllamaClient

def main():
    """Print all available models from the Ollama server."""
    print("🔍 Fetching available models...")
    
    # Create client
    client = OllamaClient()
    
    # Get models
    models = client.get_models()
    
    if models:
        print(f"✅ Found {len(models)} model(s):")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")
    else:
        print("❌ Failed to fetch models or no models available")

if __name__ == "__main__":
    main() 