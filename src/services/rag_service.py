"""
RAG Service - Simple Keyword-Based Search
No ChromaDB or ONNX models - uses TF-IDF style keyword matching.
"""
import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
import math
from src.infra.cache import redis_cache


@dataclass
class SearchResult:
    """Search result with document and relevance info."""
    doc_id: str
    title: str
    content: str
    summary: str
    tags: List[str]
    score: float
    chunk_id: Optional[str] = None
    highlight: Optional[str] = None


class RAGService:
    """Simple RAG service using TF-IDF keyword matching (no external dependencies)."""
    
    def __init__(self):
        """Initialize the RAG service."""
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.mock_data_path = self.base_dir / "mock_data" / "internal_docs_metadata.json"
        
        self.documents = []
        self.doc_index = {}  # Fast lookup by doc_id
        self.idf_scores = {}  # IDF scores for terms
        self.doc_term_freq = {}  # Term frequency per document
        
        self._load_documents()
        self._build_index()
    
    def _load_documents(self):
        """Load documents from JSON file."""
        try:
            if self.mock_data_path.exists():
                with open(self.mock_data_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                    # Build index
                    self.doc_index = {doc.get("doc_id", ""): doc for doc in self.documents}
        except Exception as e:
            print(f"Error loading documents: {e}")
            self.documents = []
            self.doc_index = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization - lowercase and split on non-alphanumeric."""
        if not text:
            return []
        text = text.lower()
        # Split on non-alphanumeric, keep meaningful tokens
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        # Filter stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                      'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                      'could', 'should', 'may', 'might', 'must', 'shall', 'this', 'that',
                      'these', 'those', 'it', 'its', 'they', 'them', 'their', 'we', 'our'}
        return [t for t in tokens if t not in stop_words and len(t) > 2]
    
    def _build_index(self):
        """Build TF-IDF index for all documents."""
        if not self.documents:
            return
        
        # Count document frequency for each term
        doc_freq = Counter()
        
        for doc in self.documents:
            doc_id = doc.get("doc_id", "")
            
            # Get all text from document
            title = doc.get("title", "")
            summary = doc.get("summary", "")
            content = doc.get("content", "")
            tags = " ".join(doc.get("tags", []))
            
            full_text = f"{title} {title} {title} {summary} {summary} {content} {tags} {tags}"
            tokens = self._tokenize(full_text)
            
            # Store term frequency for this document
            self.doc_term_freq[doc_id] = Counter(tokens)
            
            # Update document frequency (count unique terms per doc)
            unique_terms = set(tokens)
            doc_freq.update(unique_terms)
        
        # Calculate IDF scores
        num_docs = len(self.documents)
        for term, freq in doc_freq.items():
            self.idf_scores[term] = math.log((num_docs + 1) / (freq + 1)) + 1
    
    def _calculate_tfidf_score(self, query_tokens: List[str], doc_id: str) -> float:
        """Calculate TF-IDF similarity score."""
        if doc_id not in self.doc_term_freq:
            return 0.0
        
        doc_tf = self.doc_term_freq[doc_id]
        score = 0.0
        
        for token in query_tokens:
            tf = doc_tf.get(token, 0)
            idf = self.idf_scores.get(token, 1.0)
            score += tf * idf
        
        # Normalize by document length
        doc_length = sum(doc_tf.values()) or 1
        return score / math.sqrt(doc_length)
    
    def search(self, query: str, n_results: int = 5, filter_tags: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Search internal documents using TF-IDF keyword matching.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_tags: Optional list of tags to filter by
        
        Returns:
            List of SearchResult objects
        """
        if not self.documents:
            return []
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        scored_docs = []
        
        for doc in self.documents:
            doc_id = doc.get("doc_id", "")
            
            # Filter by tags if specified
            if filter_tags:
                doc_tags = [t.lower() for t in doc.get("tags", [])]
                if not any(t.lower() in doc_tags for t in filter_tags):
                    continue
            
            # Calculate TF-IDF score
            score = self._calculate_tfidf_score(query_tokens, doc_id)
            
            # Boost for exact phrase matches in title
            title_lower = doc.get("title", "").lower()
            query_lower = query.lower()
            if query_lower in title_lower:
                score *= 2.0
            
            # Boost for tag matches
            for tag in doc.get("tags", []):
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score *= 1.5
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score and return top results
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Normalize scores to 0-1 range
        max_score = scored_docs[0][0] if scored_docs else 1
        
        results = []
        for score, doc in scored_docs[:n_results]:
            normalized_score = min(1.0, score / max_score) if max_score > 0 else 0
            
            # Create highlight from summary
            summary = doc.get("summary", "")
            highlight = summary[:300] + "..." if len(summary) > 300 else summary
            
            results.append(SearchResult(
                doc_id=doc.get("doc_id", ""),
                title=doc.get("title", ""),
                summary=summary,
                content=doc.get("content", ""),
                tags=doc.get("tags", []),
                score=normalized_score,
                highlight=highlight
            ))
        
        return results
    
    def hybrid_search(self, query: str, n_results: int = 5) -> List[SearchResult]:
        """
        Enhanced search with multiple matching strategies.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            Combined and re-ranked results
        """
        # Use main search (already uses TF-IDF)
        return self.search(query, n_results)
    
    def get_document(self, doc_id: str) -> Optional[dict]:
        """Get a specific document by ID."""
        return self.doc_index.get(doc_id.upper()) or self.doc_index.get(doc_id)
    
    def list_by_tag(self, tag: str) -> List[dict]:
        """List all documents with a specific tag."""
        return [
            doc for doc in self.documents
            if tag.lower() in [t.lower() for t in doc.get("tags", [])]
        ]
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags from documents."""
        tags = set()
        for doc in self.documents:
            tags.update(doc.get("tags", []))
        return sorted(list(tags))
    
    def add_document(self, doc: Dict[str, Any]) -> bool:
        """
        Add a new document to the index.
        
        Args:
            doc: Document dictionary with doc_id, title, summary, content, tags
        
        Returns:
            Success status
        """
        try:
            doc_id = doc.get("doc_id", f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            doc["doc_id"] = doc_id
            
            # Add to in-memory storage
            self.documents.append(doc)
            self.doc_index[doc_id] = doc
            
            # Save to file
            with open(self.mock_data_path, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2)
            
            # Rebuild index
            self._build_index()
            
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
    def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get relevant context for a query to use in LLM prompts.
        
        Args:
            query: The user query
            max_tokens: Approximate max tokens for context
        
        Returns:
            Formatted context string
        """
        results = self.search(query, n_results=5)
        
        if not results:
            return ""
        
        context_parts = []
        char_count = 0
        max_chars = max_tokens * 4  # Rough approximation
        
        for result in results:
            doc_context = f"""
---
Document: {result.title}
Tags: {', '.join(result.tags)}
Relevance: {result.score:.2f}

{result.summary}

{result.content[:500] if result.content else result.highlight}
---
"""
            if char_count + len(doc_context) > max_chars:
                break
            
            context_parts.append(doc_context)
            char_count += len(doc_context)
        
        if context_parts:
            return "## Relevant Internal Documents:\n" + "\n".join(context_parts)
        return ""


# Global instance
_rag_service = None


def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def search_documents(query: str, n_results: int = 5) -> List[SearchResult]:
    """Convenience function to search documents."""
    return get_rag_service().search(query, n_results)


def get_rag_context(query: str, max_tokens: int = 2000) -> str:
    """Convenience function to get RAG context for a query."""
    cache_key = f"rag:ctx:{hash(query)}"
    if redis_cache:
        cached = redis_cache.get(cache_key)
        if cached:
            return cached
    ctx = get_rag_service().get_context_for_query(query, max_tokens)
    if ctx and redis_cache:
        redis_cache.set(cache_key, ctx, ttl_seconds=1800)
    return ctx
