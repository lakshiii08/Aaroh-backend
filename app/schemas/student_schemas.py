from typing import Optional, List
from pydantic import BaseModel, Field

class CreateStudentRequest(BaseModel):
    name: str = Field(..., description="Student full name, e.g. 'Rahul Murmu'")
    class_grade: int = Field(..., ge=1, le=12, description="Class / Grade level (1-5 for primary)")
    roll_number: str = Field(..., description="Roll number unique within the school and class, e.g. '27'")
    village: Optional[str] = Field("Bhamragad", description="Village of student")
    section: Optional[str] = Field("A", description="Optional section/division")
    school_id: Optional[str] = Field(None, description="School ID (defaults to authenticated teacher's school)")

class CreateStudentResponse(BaseModel):
    student_id: str
    name: str
    roll_number: str
    login_id: str
    temporary_password: str
    school_id: str
    grade_level: int
    message: str = "Student created successfully. Secure temporary password displayed once."

class ResetStudentPasswordResponse(BaseModel):
    student_id: str
    roll_number: str
    login_id: str
    temporary_password: str
    message: str = "Password reset successfully. New temporary password displayed once."

class StudentListItem(BaseModel):
    student_id: str
    name: str
    roll_number: str
    grade_level: int
    section: Optional[str] = None
    village: Optional[str] = None
    school_id: str
    total_xp: int = 0
    level: int = 1
    current_streak_days: int = 1
    created_at: str

class StudentDetailResponse(BaseModel):
    student_id: str
    user_id: str
    name: str
    roll_number: str
    grade_level: int
    section: Optional[str] = None
    village: Optional[str] = None
    school_id: str
    total_xp: int = 0
    level: int = 1
    current_streak_days: int = 1
    concepts_mastered: List[str] = []
    badges_count: int = 0
    created_at: str
