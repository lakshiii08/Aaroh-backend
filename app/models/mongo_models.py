from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

class UserDocument(BaseModel):
    user_id: str
    email: Optional[str] = None
    hashed_password: str
    role: str  # ADMIN, DISTRICT_ADMIN, TEACHER, STUDENT, PARENT
    school_id: Optional[str] = None
    district_id: Optional[str] = None
    name: str
    is_active: bool = True
    is_demo: bool = False
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class StudentDocument(BaseModel):
    student_id: str
    user_id: str
    roll_number: str
    school_id: str
    district_id: Optional[str] = None
    grade_level: int
    section: Optional[str] = None
    village: Optional[str] = None
    created_by_teacher_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeacherDocument(BaseModel):
    teacher_id: str
    user_id: str
    school_id: str
    district_id: Optional[str] = None
    employee_id: Optional[str] = None
    assigned_grades: List[int] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SchoolDocument(BaseModel):
    school_id: str
    school_name: str
    school_code: str
    district_id: str
    village: Optional[str] = None
    state: str = "Chhattisgarh"
    total_students: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionDocument(BaseModel):
    session_id: str
    token_jti: str
    user_id: str
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
