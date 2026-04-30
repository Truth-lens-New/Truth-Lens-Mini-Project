"""
TruthLens Check Model

SQLAlchemy model for storing analysis results.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Check(Base):
    """Check model for storing claim analysis results."""
    
    __tablename__ = "checks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Input data
    input_text = Column(Text, nullable=True)
    input_url = Column(String(2048), nullable=True)
    
    # Extracted claim
    claim = Column(Text, nullable=True)
    
    # Analysis results
    domain_score = Column(String(50), nullable=True)  # trusted, mixed, low, unknown
    factcheck_rating = Column(String(100), nullable=True)
    factcheck_summary = Column(Text, nullable=True)
    
    # Stance analysis
    stance_summary = Column(JSON, nullable=True)  # {"supports": 2, "refutes": 1, ...}
    
    # Strategy-specific metadata (e.g., heatmaps, probability breakdowns)
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    # Final verdict
    verdict = Column(String(100), nullable=False)  # Likely True, Likely False, etc.
    confidence = Column(String(20), nullable=False)  # high, medium, low
    
    # Explanation
    explanation = Column(Text, nullable=True)
    
    # Claim type (for categorization)
    claim_type = Column(String(50), nullable=True, default="GENERAL")
    
    # Pipeline version
    pipeline_version = Column(String(20), nullable=True, default="0.1.0")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="checks")
    
    def __repr__(self):
        return f"<Check(id={self.id}, verdict={self.verdict})>"
