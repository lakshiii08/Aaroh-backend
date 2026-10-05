from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.mongodb import get_mongo_db
from app.services.auth_service import AuthService
from app.schemas.auth_schemas import (
    TeacherSignupRequest,
    LoginRequest,
    StudentLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    UserProfileResponse,
)
from app.schemas.common_schemas import success_response
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])

@router.post("/teacher/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def teacher_signup(
    request: TeacherSignupRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Registers a new verified Teacher account in MongoDB."""
    service = AuthService(db)
    result = await service.signup_teacher(request.model_dump())
    return success_response(result)

@router.post("/login", response_model=dict)
async def login(
    request: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Authenticates either:
    1. Teacher / Admin / Parent via Email + Password
    2. Student via Roll Number (Login ID) + School Code + Auto-generated Password
    """
    service = AuthService(db)
    result = await service.login(
        login_id=request.login_id,
        password=request.password,
        school_code=request.school_code,
    )
    return success_response(result)

@router.post("/student-login", response_model=dict)
async def student_login(
    request: StudentLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Authenticates Student via Roll Number + Password + School Code."""
    service = AuthService(db)
    result = await service.login(
        login_id=request.roll_number,
        password=request.password,
        school_code=request.school_code,
    )
    return success_response(result)

@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Refreshes an expired access token using a valid refresh token."""
    service = AuthService(db)
    result = await service.refresh_access_token(request.refresh_token)
    return success_response(result)

@router.post("/logout", response_model=dict)
async def logout(
    request: LogoutRequest = LogoutRequest(),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Logs out user and invalidates session token."""
    service = AuthService(db)
    result = await service.logout(
        user_id=current_user["user_id"],
        token_jti=current_user.get("token_jti"),
    )
    return success_response(result)

@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
):
    """Retrieves authenticated user profile claims."""
    return success_response({
        "user_id": current_user["user_id"],
        "name": current_user["name"],
        "email": current_user.get("email"),
        "role": current_user["role"],
        "school_id": current_user.get("school_id"),
        "district_id": current_user.get("district_id"),
        "is_active": current_user.get("is_active", True),
    })
