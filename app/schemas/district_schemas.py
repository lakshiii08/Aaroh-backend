from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GeneratePathwayRequest(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    student_name: str = Field("Student", description="Student full name")
    concept_code: str = Field(..., description="Concept code, e.g. 'EVS-G3-WAT-01'")
    weak_bloom_level: str = Field("Understand", description="Identified gap level: 'Remember' | 'Understand' | 'Apply'")
    target_language: str = Field("hi", description="Instruction language")

class PathwayStepItem(BaseModel):
    step_number: int
    step_type: str
    title: str
    instruction: str
    resource_url: Optional[str] = None
    is_completed: bool

class RemedialPathwayResponse(BaseModel):
    pathway_id: str
    student_id: str
    student_name: str
    concept_code: str
    concept_name: Optional[str] = None
    weak_bloom_level: str
    status_code: str
    steps: List[PathwayStepItem]

class SendParentAdvisoryRequest(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    student_name: str = Field("Student", description="Student full name")
    parent_phone: str = Field(..., description="Parent phone number for IVR / WhatsApp audio")
    concept_code: str = Field(..., description="Concept code learned today")
    target_language: str = Field("hi", description="Parent spoken language")
    target_dialect: Optional[str] = Field("gon", description="Parent mother-tongue dialect")

class ParentAdvisoryResponse(BaseModel):
    advisory_id: str
    student_id: str
    parent_phone: str
    target_language: str
    speech_script: str
    audio_stream_url: Optional[str] = None
    dispatch_status: str

class PendingInterventionsResponse(BaseModel):
    total_pending_interventions: int
    interventions: List[Dict[str, Any]]

class DistrictAnalyticsOverviewResponse(BaseModel):
    district_analytics: Dict[str, Any]
