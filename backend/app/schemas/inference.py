"""
Pydantic Schemas for Inference Requests, Results, and Clinical Hospital Reports.
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


class PatientInfo(BaseModel):
    patient_id: str = "PT-8042-DEID"
    accession_number: str = "ACC-2026-X99"
    study_id: str = "STD-THORAX-01"
    body_region: str = "Thorax / Chest (PA View)"
    exam_description: str = "Chest Radiograph to Computed Tomography Synthesis"
    referring_physician: str = "Dr. Marcus Vance, MD (Pulmonary Medicine)"
    clinical_indication: str = "Computational exploration of axial soft tissue attenuation"
    study_date: datetime = Field(default_factory=datetime.utcnow)


class HospitalInfo(BaseModel):
    institution_name: str = "St. Jude Biomedical Research & Imaging Institute"
    department: str = "Department of Radiology & Computational Imaging"
    accreditation: str = "Investigational Research Facility (IRB Approved)"
    reporting_radiologist: str = "Dr. Elena Rostova, MD, PhD (Diagnostic Radiology / AI Core)"


class QuantitativeAttenuationAnalysis(BaseModel):
    estimated_mean_lung_hu: float = -742.5
    estimated_mediastinum_hu: float = 42.1
    estimated_cortical_bone_hu: float = 684.0
    signal_to_noise_ratio_db: float = 18.6
    contrast_to_noise_ratio: float = 3.8
    structural_fidelity_index: float = 0.884
    density_distribution: Dict[str, float] = Field(
        default_factory=lambda: {
            "Air_Hypodense_pct": 34.2,
            "Soft_Tissue_pct": 51.5,
            "Dense_Bone_pct": 14.3,
        }
    )


class RadiologicStructuredFindings(BaseModel):
    osseous_structures: str = (
        "Thoracic cage symmetry preserved. Vertebral column alignment maintained without gross deformity. "
        "Cortical bone contours intact along posterior and lateral rib segments."
    )
    cardiovascular_mediastinum: str = (
        "Cardiac silhouette transverse diameter within expected anatomical ratio (<0.50). "
        "Mediastinal contour symmetric with clear aortic knob definition."
    )
    lung_parenchyma_pleura: str = (
        "Bilateral lung fields demonstrate physiologic radiolucency. "
        "Costophrenic angles sharp and clear. No evidence of gross pleural effusion or pneumothorax."
    )
    ai_synthesis_observations: str = (
        "Deep pix2pix U-Net model successfully mapped planar radiologic shadows to a mid-thoracic axial slice (T5-T6). "
        "Central airway bifurcation and posterior vertebral body show coherent cross-sectional attenuation."
    )
    overall_impression: str = (
        "UNREMARKABLE INVESTIGATIONAL THORACIC TRANSLATION. "
        "AI-generated axial CT representation demonstrates coherent anatomical spatial correspondence with input radiograph. "
        "Research visualization only — non-diagnostic."
    )


class ClinicalReportData(BaseModel):
    job_id: str
    created_at: datetime
    model_version: str
    status: str
    input_image_url: str
    output_image_url: Optional[str] = None
    difference_map_url: Optional[str] = None
    hospital: HospitalInfo = Field(default_factory=HospitalInfo)
    patient: PatientInfo = Field(default_factory=PatientInfo)
    attenuation_analysis: QuantitativeAttenuationAnalysis = Field(default_factory=QuantitativeAttenuationAnalysis)
    findings: RadiologicStructuredFindings = Field(default_factory=RadiologicStructuredFindings)
    signoff_status: str = "PRELIMINARY_RESEARCH"
    disclaimer: str = (
        "INVESTIGATIONAL PROTOTYPE: This hospital imaging report and associated cross-sectional CT representations "
        "were synthesized using deep learning image-to-image translation (pix2pix). They are NOT clinically validated "
        "Computed Tomography scans and MUST NOT be used for primary diagnostic interpretation, treatment planning, "
        "or patient management decisions."
    )


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
