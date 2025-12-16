"""
Conversation Memory Service.
Persists chat history to database for cross-session memory.
"""
from datetime import datetime
from typing import Optional, List, Dict

from ..database.db import get_db_session
from ..database.models import Conversation, Message


class ConversationService:
    """Handle conversation persistence and retrieval."""
    
    @staticmethod
    def create_conversation(user_id: int, title: Optional[str] = None) -> int:
        """Create a new conversation and return its ID."""
        with get_db_session() as db:
            conv = Conversation(
                user_id=user_id,
                title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(conv)
            db.flush()  # Get the ID
            return conv.id
    
    @staticmethod
    def add_message(conversation_id: int, role: str, content: str, agents_used: List[str] = None) -> int:
        """Add a message to a conversation."""
        with get_db_session() as db:
            msg = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                agents_used=agents_used
            )
            db.add(msg)
            
            # Update conversation timestamp
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                conv.updated_at = datetime.utcnow()
                # Auto-generate title from first user message if not set
                if conv.title.startswith("Chat ") and role == "user":
                    conv.title = content[:50] + ("..." if len(content) > 50 else "")
            
            db.flush()
            return msg.id
    
    @staticmethod
    def get_conversation(conversation_id: int) -> Optional[Dict]:
        """Get a conversation with all messages."""
        with get_db_session() as db:
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conv:
                return None
            
            return {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "agents": msg.agents_used,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in conv.messages
                ]
            }
    
    @staticmethod
    def get_user_conversations(user_id: int, limit: int = 20, include_archived: bool = False) -> List[Dict]:
        """Get all conversations for a user."""
        with get_db_session() as db:
            query = db.query(Conversation).filter(Conversation.user_id == user_id)
            
            if not include_archived:
                query = query.filter(Conversation.is_archived == False)
            
            conversations = query.order_by(Conversation.updated_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len(conv.messages),
                    "is_archived": conv.is_archived
                }
                for conv in conversations
            ]
    
    @staticmethod
    def archive_conversation(conversation_id: int) -> bool:
        """Archive a conversation."""
        with get_db_session() as db:
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                conv.is_archived = True
                return True
            return False
    
    @staticmethod
    def delete_conversation(conversation_id: int) -> bool:
        """Permanently delete a conversation."""
        with get_db_session() as db:
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                db.delete(conv)
                return True
            return False
    
    @staticmethod
    def rename_conversation(conversation_id: int, new_title: str) -> bool:
        """Rename a conversation."""
        with get_db_session() as db:
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                conv.title = new_title[:200]  # Limit title length
                return True
            return False
    
    @staticmethod
    def get_recent_context(conversation_id: int, num_messages: int = 10) -> List[Dict]:
        """Get recent messages for context window."""
        with get_db_session() as db:
            messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(num_messages)
                .all()
            )
            
            # Return in chronological order
            return [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(messages)
            ]
    
    @staticmethod
    def search_conversations(user_id: int, query: str, limit: int = 10) -> List[Dict]:
        """Search conversations by content."""
        with get_db_session() as db:
            # Search in message content
            messages = (
                db.query(Message)
                .join(Conversation)
                .filter(Conversation.user_id == user_id)
                .filter(Message.content.ilike(f"%{query}%"))
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all()
            )
            
            # Get unique conversations
            seen_convs = set()
            results = []
            
            for msg in messages:
                if msg.conversation_id not in seen_convs:
                    seen_convs.add(msg.conversation_id)
                    conv = msg.conversation
                    results.append({
                        "id": conv.id,
                        "title": conv.title,
                        "updated_at": conv.updated_at.isoformat(),
                        "matching_message": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    })
            
            return results
