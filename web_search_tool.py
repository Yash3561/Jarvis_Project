# web_search_tool.py
import os
from tavily import TavilyClient

# Initialize the client with the API key from your .env file
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("Tavily API key not found. Please set it in your .env file.")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def search_the_web(query: str) -> str:
    """
    Uses the Tavily API to search the web for a given query.
    """
    print(f"INFO: Searching the web for: '{query}'")
    try:
        response = tavily_client.search(query=query, search_depth="basic")
        # We'll just return the top 2-3 results for conciseness
        context = "\n\n".join([obj["content"] for obj in response["results"][:3]])
        return context
    except Exception as e:
        return f"Error during web search: {e}"