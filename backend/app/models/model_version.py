"""
Model Version Entity Model.
Stores registered machine learning models and version manifests.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON

from app.models.base import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), unique=True, index=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    architecture = Column(String(100), default="pix2pix_UNet256", nullable=False)
    weights_path = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    hyperparameters = Column(JSON, nullable=True)
    evaluation_metrics = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
