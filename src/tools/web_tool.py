"""
Web Search Tool
Queries mock web search results for external intelligence.
"""
import json
from crewai.tools import tool
from pathlib import Path


def _load_web_data() -> list:
    """Load web search mock data from JSON file."""
    data_path = Path(__file__).resolve().parent.parent.parent / "mock_data" / "web_search_results.json"
    with open(data_path, "r") as f:
        return json.load(f)


@tool("Web Search")
def web_search(query: str) -> str:
    """
    Search the web for pharmaceutical news, approvals, and market intelligence.
    
    Args:
        query: Search query (e.g., 'Pembrolizumab new indications', 'generic launch India')
    
    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        data = _load_web_data()
        query_lower = query.lower()
        
        best_match = None
        best_score = 0
        
        # Find best matching query in mock data
        for entry in data:
            stored_query = entry.get("query", "").lower()
            score = 0
            
            # Check for word overlap
            query_words = set(query_lower.split())
            stored_words = set(stored_query.split())
            overlap = len(query_words & stored_words)
            score = overlap
            
            if score > best_score:
                best_score = score
                best_match = entry
        
        if not best_match or best_score < 1:
            return f"No web search results found for: '{query}'. Try different keywords."
        
        results = best_match.get("results", [])
        
        if not results:
            return f"No results found for query: {query}"
        
        output = [f"**Web Search Results for: '{query}'**\n"]
        
        for i, result in enumerate(results, 1):
            output.append(
                f"{i}. **{result['title']}**\n"
                f"   🔗 {result['url']}\n"
                f"   {result['snippet']}\n"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error performing web search: {str(e)}"


@tool("Get Recent News")
def get_recent_news(topic: str) -> str:
    """
    Get recent pharmaceutical news on a specific topic.
    
    Args:
        topic: Topic to get news for (e.g., 'respiratory', 'patent expiry', 'FDA approval')
    
    Returns:
        Recent news articles related to the topic.
    """
    try:
        data = _load_web_data()
        topic_lower = topic.lower()
        
        all_results = []
        
        for entry in data:
            for result in entry.get("results", []):
                # Check if topic appears in title or snippet
                if (topic_lower in result.get("title", "").lower() or 
                    topic_lower in result.get("snippet", "").lower()):
                    all_results.append(result)
        
        if not all_results:
            return f"No recent news found for topic: '{topic}'"
        
        output = [f"**Recent News on '{topic}':**\n"]
        
        for result in all_results[:5]:
            output.append(
                f"📰 **{result['title']}**\n"
                f"   {result['snippet']}\n"
                f"   🔗 {result['url']}\n"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error getting news: {str(e)}"
