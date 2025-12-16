"""
Query Tracking Service for Analytics.
Logs all queries for dashboard analytics.
"""
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import func, desc

from src.database.db import get_db_session
from src.database.models import QueryLog, User


class QueryTracker:
    """Track and analyze user queries."""
    
    @staticmethod
    def log_query(
        query_text: str,
        agents_used: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> int:
        """Log a query and return its ID."""
        try:
            with get_db_session() as db:
                log = QueryLog(
                    user_id=user_id,
                    query_text=query_text,
                    agents_used=agents_used or [],
                    response_time_ms=response_time_ms,
                    success=success,
                    error_message=error_message
                )
                db.add(log)
                db.flush()  # Get the ID before commit
                return log.id
        except Exception as e:
            print(f"Error logging query: {e}")
            return -1
    
    @staticmethod
    def get_total_queries(days: int = 30) -> int:
        """Get total query count for period."""
        try:
            with get_db_session() as db:
                since = datetime.utcnow() - timedelta(days=days)
                count = db.query(func.count(QueryLog.id)).filter(
                    QueryLog.created_at >= since
                ).scalar()
                return count or 0
        except Exception:
            return 0
    
    @staticmethod
    def get_queries_by_day(days: int = 30) -> List[Dict[str, Any]]:
        """Get query counts grouped by day."""
        try:
            with get_db_session() as db:
                since = datetime.utcnow() - timedelta(days=days)
                results = db.query(
                    func.date(QueryLog.created_at).label('date'),
                    func.count(QueryLog.id).label('count')
                ).filter(
                    QueryLog.created_at >= since
                ).group_by(
                    func.date(QueryLog.created_at)
                ).order_by('date').all()
                
                return [{"date": str(r.date), "count": r.count} for r in results]
        except Exception:
            return []
    
    @staticmethod
    def get_agent_distribution(days: int = 30) -> Dict[str, int]:
        """Get count of queries per agent."""
        try:
            with get_db_session() as db:
                since = datetime.utcnow() - timedelta(days=days)
                logs = db.query(QueryLog.agents_used).filter(
                    QueryLog.created_at >= since,
                    QueryLog.agents_used.isnot(None)
                ).all()
                
                distribution = {}
                for log in logs:
                    if log.agents_used:
                        for agent in log.agents_used:
                            distribution[agent] = distribution.get(agent, 0) + 1
                
                return distribution
        except Exception:
            return {}
    
    @staticmethod
    def get_popular_queries(limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """Get most common query patterns."""
        try:
            with get_db_session() as db:
                since = datetime.utcnow() - timedelta(days=days)
                
                # Get all queries and find common themes
                logs = db.query(QueryLog.query_text).filter(
                    QueryLog.created_at >= since
                ).order_by(desc(QueryLog.created_at)).limit(100).all()
                
                # Simple keyword extraction
                keywords = {}
                for log in logs:
                    words = log.query_text.lower().split()
                    for word in words:
                        if len(word) > 4 and word not in ['about', 'what', 'which', 'where', 'there']:
                            keywords[word] = keywords.get(word, 0) + 1
                
                # Get top keywords
                sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:limit]
                return [{"keyword": k, "count": v} for k, v in sorted_keywords]
        except Exception:
            return []
    
    @staticmethod
    def get_recent_queries(limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent queries with details."""
        try:
            with get_db_session() as db:
                logs = db.query(QueryLog).order_by(
                    desc(QueryLog.created_at)
                ).limit(limit).all()
                
                return [{
                    "id": log.id,
                    "query": log.query_text[:100] + "..." if len(log.query_text) > 100 else log.query_text,
                    "agents": log.agents_used or [],
                    "time_ms": log.response_time_ms,
                    "success": log.success,
                    "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M")
                } for log in logs]
        except Exception:
            return []
    
    @staticmethod
    def get_success_rate(days: int = 30) -> float:
        """Get query success rate as percentage."""
        try:
            with get_db_session() as db:
                since = datetime.utcnow() - timedelta(days=days)
                total = db.query(func.count(QueryLog.id)).filter(
                    QueryLog.created_at >= since
                ).scalar() or 0
                
                if total == 0:
                    return 100.0
                
                successful = db.query(func.count(QueryLog.id)).filter(
                    QueryLog.created_at >= since,
                    QueryLog.success == True
                ).scalar() or 0
                
                return round((successful / total) * 100, 1)
        except Exception:
            return 100.0
    
    @staticmethod
    def get_avg_response_time(days: int = 30) -> float:
        """Get average response time in milliseconds."""
        try:
            with get_db_session() as db:
                since = datetime.utcnow() - timedelta(days=days)
                avg = db.query(func.avg(QueryLog.response_time_ms)).filter(
                    QueryLog.created_at >= since,
                    QueryLog.response_time_ms.isnot(None)
                ).scalar()
                
                return round(avg, 0) if avg else 0
        except Exception:
            return 0
    
    @staticmethod
    def get_user_query_stats(user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get query statistics for a specific user."""
        try:
            with get_db_session() as db:
                since = datetime.utcnow() - timedelta(days=days)
                
                total = db.query(func.count(QueryLog.id)).filter(
                    QueryLog.user_id == user_id,
                    QueryLog.created_at >= since
                ).scalar() or 0
                
                successful = db.query(func.count(QueryLog.id)).filter(
                    QueryLog.user_id == user_id,
                    QueryLog.created_at >= since,
                    QueryLog.success == True
                ).scalar() or 0
                
                return {
                    "total_queries": total,
                    "successful": successful,
                    "success_rate": round((successful / total * 100), 1) if total > 0 else 100.0
                }
        except Exception:
            return {"total_queries": 0, "successful": 0, "success_rate": 100.0}
