import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('/home/jake/Code/.env', override=True)

# Path to prompt file
prompt_file = "/home/jake/Code/VSP2/ai_authorization_instruction.txt"


class AIAgent:
    def __init__(self, prompt_file):
        """Initialize the AI agent and load the API key."""
        self.client = openai
        self.client.api_key = os.getenv("OPENAI_API_KEY")
        self.prompt_file = prompt_file
        self.model_name = "gpt-4o-mini"  # Use the latest and cheapest model

    def chat(self, input_data):
        """Send input to the AI and return a response."""
        # Load the prompt file content
        with open(self.prompt_file, "r") as file:
            prompt_content = file.read().strip()

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": input_data},
            ],
            temperature=0.7
        )

        reply = response.choices[0].message.content.strip()
        return reply


# Example usage:
if __name__ == "__main__":
    agent = AIAgent(prompt_file)

    input_data = "John Doe, 1234, 01/01/1990, Jane Doe (Primary Account Holder)"
    result = agent.chat(input_data)

    print("AI Output:", result)
