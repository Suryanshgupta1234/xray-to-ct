"""
Pydantic Schemas for Inference Requests & Results.
"""

from typing import Optional, Dict, Any, List, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIErrorDetails(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class StandardResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: Optional[DataT] = None
    message: str = "Operation successful"


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: APIErrorDetails


class InferenceJobResponseData(BaseModel):
    id: str
    user_id: str
    status: str
    model_version: str
    original_filename: Optional[str] = None
    image_format: str
    input_image_url: str
    output_image_url: Optional[str] = None
    difference_map_url: Optional[str] = None
    processing_time_ms: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    disclaimer: str = Field(
        default=(
            "RESEARCH ONLY: Generated image is an AI statistical approximation and is NOT a clinical CT scan. "
            "Must NOT be used for clinical diagnosis, treatment decisions, or patient care."
        )
    )

    model_config = {"from_attributes": True}


class InferenceListResponseData(BaseModel):
    items: List[InferenceJobResponseData]
    total: int
    page: int
    page_size: int
