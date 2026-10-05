from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

class TeacherSignupRequest(BaseModel):
    name: str = Field(..., description="Full Name of Teacher")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=6, description="Teacher secure password")
    school_id: str = Field(..., description="School ID or Code where teacher teaches")
    district_id: Optional[str] = Field("CG_BASTAR_01", description="District ID")
    employee_id: Optional[str] = Field(None, description="Government Teacher Employee ID")
    assigned_grades: List[int] = Field(default=[3, 4, 5], description="Grade levels taught")
    subjects: List[str] = Field(default=["Environmental Studies", "Mathematics"], description="Subjects taught")

class LoginRequest(BaseModel):
    login_id: str = Field(..., description="Teacher/Admin Email OR Student Roll Number")
    password: str = Field(..., description="Password (for student, auto-generated password)")
    school_code: Optional[str] = Field(None, description="Required for student login to resolve school context")

class StudentLoginRequest(BaseModel):
    roll_number: str = Field(..., description="Student Roll Number / Login ID")
    password: str = Field(..., description="Auto-generated Password or PIN")
    school_code: Optional[str] = Field(None, description="School Code")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    name: str
    school_id: Optional[str] = None
    district_id: Optional[str] = None
    roll_number: Optional[str] = None
    must_change_password: bool = False

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None

class UserProfileResponse(BaseModel):
    user_id: str
    name: str
    email: Optional[str] = None
    role: str
    school_id: Optional[str] = None
    district_id: Optional[str] = None
    roll_number: Optional[str] = None
    grade_level: Optional[int] = None
    village: Optional[str] = None
    is_active: bool
