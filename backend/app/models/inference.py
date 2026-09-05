"""
Inference Job Entity Model.
Tracks inference requests, stored file paths, execution latency, and model versions.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class InferenceStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InferenceJob(Base):
    __tablename__ = "inference_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    input_image_path = Column(String(500), nullable=False)
    output_image_path = Column(String(500), nullable=True)
    original_filename = Column(String(255), nullable=True)
    image_format = Column(String(50), default="PNG")

    model_version = Column(String(50), default="v1", nullable=False, index=True)
    status = Column(String(50), default=InferenceStatus.PENDING, nullable=False, index=True)
    processing_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="inference_jobs")
