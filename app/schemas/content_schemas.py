from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

class ContentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    total_pages: int
    total_chunks: int
    total_concepts: int

class DocumentListItem(BaseModel):
    id: str
    filename: str
    title: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[int] = None
    language: Optional[str] = None
    summary: Optional[str] = None
    total_pages: int = 0
    status: str
    created_at: Optional[str] = None

class ConceptItem(BaseModel):
    id: str
    concept_code: str
    name: str
    definition: str
    blooms_level: str
    difficulty_level: int
    prerequisite_concepts: List[str] = []
    rural_tribal_anchors: List[str] = []
    key_vocabulary: List[str] = []

class DocumentConceptsResponse(BaseModel):
    document_id: str
    title: Optional[str] = None
    total_concepts: int
    concepts: List[ConceptItem]

class ContentSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query across curriculum")
    top_k: int = Field(5, description="Number of results to retrieve")
    grade_level: Optional[int] = Field(None, description="Optional grade filter")
    subject: Optional[str] = Field(None, description="Optional subject filter")

class ContentSearchResultItem(BaseModel):
    chunk_id: str
    content: str
    page_number: int
    chunk_index: int
    concept_code: Optional[str] = None
    similarity_score: float
    doc_title: Optional[str] = None
    grade_level: Optional[int] = None
    subject: Optional[str] = None

class ContentSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[ContentSearchResultItem]
