"""Simple Chat Agent - A lightweight conversational agent.

This agent is designed for quick Q&A and general conversation,
without the deep research capabilities of the research agent.
"""

from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

# Simple system prompt for conversational agent
CHAT_INSTRUCTIONS = """You are a helpful and friendly AI assistant.

Your role:
- Answer questions clearly and concisely
- Provide helpful information
- Engage in natural conversation
- Be honest when you don't know something

Keep responses focused and avoid unnecessary complexity."""

# Create a simple chat agent without sub-agents or complex tools
# This is a lighter-weight agent compared to the research agent
chat_agent = create_deep_agent(
    model=ChatOpenAI(model="gpt-4o"),
    tools=[],  # No tools - just conversational
    system_prompt=CHAT_INSTRUCTIONS,
    # No subagents - keep it simple
)

