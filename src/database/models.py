"""
SQLAlchemy Database Models for Pharma Agentic AI.
Replaces JSON mock data with proper relational database.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


# --- Enums ---
class UserRole(enum.Enum):
    ANALYST = "analyst"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    ADMIN = "admin"


class PatentStatus(enum.Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    PENDING = "Pending"


# --- User & Auth ---
class User(Base):
    """User accounts with role-based access."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ANALYST, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Rate limiting fields
    api_calls_today = Column(Integer, default=0)
    api_calls_reset_at = Column(DateTime, nullable=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"


# --- Conversation Memory ---
class Conversation(Base):
    """Chat conversation sessions."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self):
        return f"<Conversation {self.id}: {self.title}>"


class Message(Base):
    """Individual chat messages within a conversation."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    agents_used = Column(JSON, nullable=True)  # List of agents that handled query
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.role}: {self.content[:50]}...>"


# --- Pharma Data Models ---
class MarketData(Base):
    """IQVIA-style market data."""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    molecule = Column(String(100), nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)
    therapy_area = Column(String(100), nullable=False, index=True)
    indication = Column(String(200), nullable=True)
    market_size_usd_mn = Column(Float, nullable=False)
    cagr_percent = Column(Float, nullable=False)
    top_competitors = Column(JSON, nullable=True)  # List of competitor names
    generic_penetration = Column(String(20), nullable=True)  # Low/Medium/High
    patient_burden = Column(String(20), nullable=True)  # Low/Medium/High/Very High
    competition_level = Column(String(20), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MarketData {self.molecule} ({self.region})>"


class Patent(Base):
    """USPTO patent data."""
    __tablename__ = "patents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    molecule = Column(String(100), nullable=False, index=True)
    patent_number = Column(String(50), nullable=False, unique=True)
    patent_type = Column(String(100), nullable=True)  # Composition of Matter, Formulation, etc.
    expiry_date = Column(DateTime, nullable=True)
    status = Column(Enum(PatentStatus), default=PatentStatus.ACTIVE)
    country = Column(String(10), default="US")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Patent {self.patent_number} ({self.molecule})>"


class ClinicalTrial(Base):
    """Clinical trials data."""
    __tablename__ = "clinical_trials"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nct_id = Column(String(20), nullable=False, unique=True, index=True)
    indication = Column(String(200), nullable=False, index=True)
    therapy_area = Column(String(100), nullable=True)
    phase = Column(String(20), nullable=False)
    drug_name = Column(String(100), nullable=False, index=True)
    sponsor = Column(String(200), nullable=True)
    patient_burden_score = Column(Float, nullable=True)
    competition_density = Column(String(20), nullable=True)
    unmet_need = Column(String(20), nullable=True)
    status = Column(String(50), default="Active")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ClinicalTrial {self.nct_id}: {self.drug_name}>"


class Competitor(Base):
    """Competitor strategy intelligence."""
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    molecule = Column(String(100), nullable=False, index=True)
    competitor_name = Column(String(200), nullable=False)
    predicted_strategy = Column(Text, nullable=True)
    likelihood = Column(String(20), nullable=True)  # Low/Medium/High
    impact = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Competitor {self.competitor_name}: {self.molecule}>"


class TradeData(Base):
    """Import/Export trade data."""
    __tablename__ = "trade_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    molecule = Column(String(100), nullable=False, index=True)
    total_import_volume_kg = Column(Float, nullable=True)
    major_source_countries = Column(JSON, nullable=True)  # List of countries
    average_price_per_kg = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TradeData {self.molecule}>"


class InternalDoc(Base):
    """Internal strategy documents metadata."""
    __tablename__ = "internal_docs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<InternalDoc {self.doc_id}: {self.title}>"


class SocialPost(Base):
    """Social media/patient voice data."""
    __tablename__ = "social_posts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    molecule = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=True)
    post_text = Column(Text, nullable=False)
    sentiment = Column(Float, nullable=True)  # -1.0 to 1.0
    therapy_area = Column(String(100), nullable=True, index=True)
    complaint_theme = Column(String(100), nullable=True)
    post_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SocialPost {self.molecule}: {self.post_text[:50]}...>"


# --- Rate Limiting & API Usage ---
class APIUsage(Base):
    """Track API usage for rate limiting."""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    api_name = Column(String(50), nullable=False)  # groq, tavily, etc.
    calls_count = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<APIUsage {self.api_name}: {self.calls_count}>"


class QueryLog(Base):
    """Track all queries for analytics."""
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    agents_used = Column(JSON, nullable=True)  # List of agents
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QueryLog {self.id}: {self.query_text[:50]}...>"
