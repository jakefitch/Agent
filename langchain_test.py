# vsp_agent.py

from langchain_community.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent, AgentType
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
print("After first load_dotenv(), OPENAI_API_KEY exists:", "OPENAI_API_KEY" in os.environ)

#point to the env file in the home folder
load_dotenv("/home/jake/Code/.env")
print("After second load_dotenv(), OPENAI_API_KEY exists:", "OPENAI_API_KEY" in os.environ)
print("OPENAI_API_KEY value:", os.environ.get("OPENAI_API_KEY", "Not found"))

# Fake placeholder for the real function
def delete_authorization(*args, **kwargs):
    print("🔥 Called: delete_authorization()")
    return "Authorization deleted"

def issue_authorization(*args, **kwargs):
    print("✅ Called: issue_authorization()")
    return "Authorization issued"

def skip(*args, **kwargs):
    print("❌ Called: skip()")
    return "No action taken"

# Define tools for agent to choose from
tools = [
    Tool(name="DeleteAuthorization", func=delete_authorization, description="Use if old authorization exists."),
    Tool(name="IssueAuthorization", func=issue_authorization, description="Use if patient needs new services authorized."),
    Tool(name="Skip", func=skip, description="Use if nothing should be done.")
]

# LLM instance (OpenAI for now)
llm = ChatOpenAI(temperature=0)

# Set up the agent
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# Pass in your current page state and let the agent decide
input_prompt = """
Patient is on a VSP plan called 'VSP Exam Plus Plan'. 
The authorization page says: 'Authorization exists for materials, but not for exam.'
What should be done?
"""

# Run it
agent.run(input_prompt)
