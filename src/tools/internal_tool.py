"""
Internal Knowledge Tool
RAG-based search over internal documents using ChromaDB.
"""
import json
from typing import Optional
from crewai.tools import tool
from pathlib import Path


def _load_internal_docs() -> list:
    """Load internal documents mock data from JSON file."""
    data_path = Path(__file__).resolve().parent.parent.parent / "mock_data" / "internal_docs_metadata.json"
    with open(data_path, "r") as f:
        return json.load(f)


@tool("Search Internal Documents")
def search_internal_docs(query: str, tags: Optional[list] = None) -> str:
    """
    Search internal strategy documents and reports.
    
    Args:
        query: Search query (keywords or natural language)
        tags: Optional list of tags to filter by (e.g., ['Oncology', 'Strategy'])
    
    Returns:
        Matching documents with summaries and relevant content.
    """
    try:
        docs = _load_internal_docs()
        results = []
        query_lower = query.lower()
        
        for doc in docs:
            score = 0
            
            # Check title match
            if query_lower in doc.get("title", "").lower():
                score += 3
            
            # Check summary match
            if query_lower in doc.get("summary", "").lower():
                score += 2
            
            # Check content match
            if query_lower in doc.get("content", "").lower():
                score += 2
            
            # Check tag match
            for tag in doc.get("tags", []):
                if query_lower in tag.lower():
                    score += 1
                if tags and tag in tags:
                    score += 2
            
            # Check for keyword matches
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 3:  # Skip short words
                    if word in doc.get("title", "").lower():
                        score += 1
                    if word in doc.get("summary", "").lower():
                        score += 1
                    if word in doc.get("content", "").lower():
                        score += 1
            
            if score > 0:
                results.append((score, doc))
        
        if not results:
            return f"No internal documents found matching: '{query}'"
        
        # Sort by relevance score
        results.sort(key=lambda x: x[0], reverse=True)
        
        output = [f"**Internal Knowledge Search Results for: '{query}'**\n"]
        
        for score, doc in results[:5]:  # Top 5 results
            output.append(
                f"**[{doc['doc_id']}] {doc['title']}**\n"
                f"  Tags: {', '.join(doc['tags'])}\n"
                f"  Summary: {doc['summary']}\n"
            )
            if doc.get("content"):
                # Truncate long content
                content = doc["content"][:300] + "..." if len(doc.get("content", "")) > 300 else doc["content"]
                output.append(f"  Content: {content}\n")
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error searching internal docs: {str(e)}"


@tool("Get Document by ID")
def get_document_by_id(doc_id: str) -> str:
    """
    Retrieve a specific internal document by its ID.
    
    Args:
        doc_id: Document ID (e.g., 'DOC-001')
    
    Returns:
        Full document content.
    """
    try:
        docs = _load_internal_docs()
        
        for doc in docs:
            if doc.get("doc_id", "").upper() == doc_id.upper():
                output = (
                    f"**{doc['title']}** ({doc['doc_id']})\n\n"
                    f"**Tags:** {', '.join(doc['tags'])}\n\n"
                    f"**Summary:**\n{doc['summary']}\n\n"
                )
                if doc.get("content"):
                    output += f"**Full Content:**\n{doc['content']}"
                return output
        
        return f"Document not found: {doc_id}"
    
    except Exception as e:
        return f"Error retrieving document: {str(e)}"


@tool("List Documents by Tag")
def list_documents_by_tag(tag: str) -> str:
    """
    List all internal documents with a specific tag.
    
    Args:
        tag: Tag to filter by (e.g., 'Respiratory', 'Strategy', 'India')
    
    Returns:
        List of matching documents.
    """
    try:
        docs = _load_internal_docs()
        
        matching = []
        for doc in docs:
            if tag.lower() in [t.lower() for t in doc.get("tags", [])]:
                matching.append(doc)
        
        if not matching:
            return f"No documents found with tag: {tag}"
        
        output = [f"**Documents tagged '{tag}':**\n"]
        
        for doc in matching:
            output.append(
                f"- **{doc['doc_id']}**: {doc['title']}\n"
                f"  {doc['summary']}\n"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error listing documents: {str(e)}"
