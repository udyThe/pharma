"""
Authentication Service for Pharma Agentic AI.
Handles user registration, login, sessions, and role-based access.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

from ..database.db import get_db_session
from ..database.models import User, UserRole


class AuthService:
    """Handle user authentication and session management."""
    
    # Session storage (in production, use Redis)
    _sessions: Dict[str, dict] = {}
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return hashlib.sha256(password.encode()).hexdigest() == hashed
    
    @classmethod
    def register(cls, username: str, email: str, password: str, role: UserRole = UserRole.ANALYST) -> tuple[bool, str]:
        """
        Register a new user.
        
        Returns:
            (success: bool, message: str)
        """
        with get_db_session() as db:
            # Check existing username
            if db.query(User).filter(User.username == username).first():
                return False, "Username already exists"
            
            # Check existing email
            if db.query(User).filter(User.email == email).first():
                return False, "Email already registered"
            
            # Validate password
            if len(password) < 4:
                return False, "Password must be at least 4 characters"
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=cls.hash_password(password),
                role=role
            )
            db.add(user)
        
        return True, f"User '{username}' registered successfully"
    
    @classmethod
    def login(cls, username: str, password: str) -> tuple[Optional[str], Optional[dict], str]:
        """
        Authenticate a user and create a session.
        
        Returns:
            (session_token: str or None, user_info: dict or None, message: str)
        """
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                return None, None, "Invalid username or password"
            
            if not user.is_active:
                return None, None, "Account is deactivated"
            
            if not cls.verify_password(password, user.password_hash):
                return None, None, "Invalid username or password"
            
            # Update last login
            user.last_login = datetime.utcnow()
            
            # Create session token
            session_token = secrets.token_hex(32)
            
            # Store session
            user_info = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            cls._sessions[session_token] = user_info
            
            return session_token, user_info, "Login successful"
    
    @classmethod
    def logout(cls, session_token: str) -> bool:
        """Invalidate a session."""
        if session_token in cls._sessions:
            del cls._sessions[session_token]
            return True
        return False
    
    @classmethod
    def get_current_user(cls, session_token: str) -> Optional[dict]:
        """Get user info from session token."""
        if session_token not in cls._sessions:
            return None
        
        session = cls._sessions[session_token]
        
        # Check expiration
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.utcnow() > expires_at:
            del cls._sessions[session_token]
            return None
        
        return session
    
    @classmethod
    def check_permission(cls, session_token: str, required_roles: list[UserRole]) -> bool:
        """Check if user has required role."""
        user = cls.get_current_user(session_token)
        if not user:
            return False
        
        user_role = UserRole(user["role"])
        return user_role in required_roles
    
    @classmethod
    def get_user_by_id(cls, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with get_db_session() as db:
            return db.query(User).filter(User.id == user_id).first()
    
    @classmethod
    def update_password(cls, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        """Update user password."""
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False, "User not found"
            
            if not cls.verify_password(old_password, user.password_hash):
                return False, "Current password is incorrect"
            
            if len(new_password) < 4:
                return False, "New password must be at least 4 characters"
            
            user.password_hash = cls.hash_password(new_password)
        
        return True, "Password updated successfully"


# Role-based access decorators
def require_roles(*roles: UserRole):
    """Decorator to require specific roles for a function."""
    def decorator(func):
        def wrapper(session_token: str, *args, **kwargs):
            user = AuthService.get_current_user(session_token)
            if not user:
                raise PermissionError("Not authenticated")
            
            user_role = UserRole(user["role"])
            if user_role not in roles:
                raise PermissionError(f"Requires one of: {[r.value for r in roles]}")
            
            return func(session_token, *args, **kwargs)
        return wrapper
    return decorator


# Convenience access levels
ANYONE = [UserRole.ANALYST, UserRole.MANAGER, UserRole.EXECUTIVE, UserRole.ADMIN]
MANAGERS_UP = [UserRole.MANAGER, UserRole.EXECUTIVE, UserRole.ADMIN]
EXECUTIVES_UP = [UserRole.EXECUTIVE, UserRole.ADMIN]
ADMIN_ONLY = [UserRole.ADMIN]
