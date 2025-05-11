# Import relevant functionality
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

import getpass
import os
import sys

def setup_api_keys():
    print("Setting up API keys...")
    
    # Google API Key
    if "GOOGLE_API_KEY" not in os.environ:
        print("\nPlease enter your Google AI API key.")
        print("You can get one from: https://makersuite.google.com/app/apikey")
        os.environ["GOOGLE_API_KEY"] = getpass.getpass("Google API Key: ").strip()
    
    # Tavily API Key
    if "TAVILY_API_KEY" not in os.environ:
        print("\nPlease enter your Tavily API key.")
        print("You can get one from: https://tavily.com/")
        os.environ["TAVILY_API_KEY"] = getpass.getpass("Tavily API Key: ").strip()
    
    # Validate keys are not empty
    if not os.environ["GOOGLE_API_KEY"] or not os.environ["TAVILY_API_KEY"]:
        print("Error: API keys cannot be empty!")
        sys.exit(1)

try:
    setup_api_keys()
    
    # Create the agent
    memory = MemorySaver()
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    search = TavilySearchResults(max_results=2)
    tools = [search]
    agent_executor = create_react_agent(model, tools, checkpointer=memory)

    # Use the agent
    config = {"configurable": {"thread_id": "abc123"}}
    for step in agent_executor.stream(
        {"messages": [HumanMessage(content="hi im bob! and i live in sf, CA")]},
        config,
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()

    for step in agent_executor.stream(
        {"messages": [HumanMessage(content="whats the weather where I live?")]},
        config,
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()

except Exception as e:
    print(f"\nAn error occurred: {str(e)}")
    print("\nPlease make sure you have valid API keys and try again.")
    sys.exit(1)