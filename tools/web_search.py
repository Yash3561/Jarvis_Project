# tools/web_search.py
import os
from tavily import TavilyClient
def search_the_web(query: str) -> str:
    try:
        api_key = os.getenv("TAVILY_API_KEY"); tavily = TavilyClient(api_key=api_key)
        response = tavily.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as e: return f"Error during web search: {e}"