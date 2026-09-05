"""
Pydantic Schemas for Model Versioning, Health Checks & System Monitoring.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel


class ModelVersionResponseData(BaseModel):
    id: str
    version: str
    model_name: str
    architecture: str
    is_active: bool
    hyperparameters: Optional[Dict[str, Any]] = None
    evaluation_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthServiceStatus(BaseModel):
    status: str  # "healthy", "degraded", "unavailable"
    details: Optional[Dict[str, Any]] = None


class SystemHealthResponseData(BaseModel):
    status: str  # "healthy", "unhealthy"
    version: str = "1.0.0"
    device: str
    api: HealthServiceStatus
    database: HealthServiceStatus
    storage: HealthServiceStatus
    model_cache: HealthServiceStatus
    timestamp: datetime


class AdminSystemStatsData(BaseModel):
    total_users: int
    total_inferences: int
    completed_inferences: int
    failed_inferences: int
    average_latency_ms: float
    active_model_version: str
    gpu_available: bool
