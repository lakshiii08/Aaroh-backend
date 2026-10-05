from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate into mother tongue")
    source_lang: str = Field("en", description="Source language code (e.g. 'en')")
    target_lang: str = Field("hi", description="Target language code (e.g. 'hi', 'bn', 'mr', 'or')")
    target_dialect: Optional[str] = Field(None, description="Optional tribal dialect: 'gon' (Gondi), 'sat' (Santhali), 'hne' (Chhattisgarhi), 'bhi' (Bhili)")
    apply_glossary: bool = Field(True, description="Whether to apply curated educational & tribal glossary")

class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    applied_glossary_terms: List[str] = []
    latency_ms: float
    backend_used: str

class BatchTranslateRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to batch translate")
    source_lang: str = Field("en", description="Source language code")
    target_lang: str = Field("hi", description="Target language code")
    target_dialect: Optional[str] = Field(None, description="Optional tribal dialect")

class BatchTranslateItem(BaseModel):
    original_text: str
    translated_text: str
    applied_glossary_terms: List[str] = []
    latency_ms: float

class BatchTranslateResponse(BaseModel):
    total_count: int
    total_time_ms: float
    results: List[BatchTranslateItem]

class GlossaryTermAddRequest(BaseModel):
    source_term: str = Field(..., description="Standard term, e.g. 'Photosynthesis' or 'Well'")
    translated_term: str = Field(..., description="Target translation")
    source_lang: str = Field("en", description="Source language")
    target_lang: str = Field("hi", description="Target language")
    domain: str = Field("general", description="Subject domain: 'evs', 'math', 'general'")
    dialects: Dict[str, str] = Field(default_factory=dict, description="Tribal dialect mappings: {'gon': '...', 'sat': '...'}")
    phonetic_hint: Optional[str] = None
    notes: Optional[str] = None

class GlossaryLookupResponse(BaseModel):
    term: Dict[str, Any]

class TranslateLessonRequest(BaseModel):
    target_lang: str = Field("hi", description="Target language code")
    target_dialect: Optional[str] = Field(None, description="Optional tribal dialect: 'gon', 'sat'")

class TranslatedChunkItem(BaseModel):
    chunk_index: int
    page_number: int
    original_content: str
    translated_content: str
    applied_glossary_terms: List[str] = []

class TranslateLessonResponse(BaseModel):
    document_id: str
    document_title: Optional[str] = None
    target_lang: str
    target_dialect: Optional[str] = None
    total_chunks: int
    total_time_ms: float
    chunks: List[TranslatedChunkItem]
