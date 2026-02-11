"""
TruthLens User Model

SQLAlchemy model for user authentication.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to checks
    checks = relationship("Check", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
