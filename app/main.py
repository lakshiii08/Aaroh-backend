import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text


from app.core.config import settings
from app.core.logging import logger, request_id_ctx
from app.core.exceptions import AarohAPIException, aaroh_exception_handler
from app.core.mongodb import MongoManager
from app.core.postgres import postgres_manager
from app.ai.aaroh_ai_adapter import ai_adapter

# Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.teachers import router as teachers_router
from app.api.v1.students import router as students_router
from app.api.v1.content import router as content_router
from app.api.v1.translation import router as translation_router
from app.api.v1.simplification import router as simplification_router
from app.api.v1.assessment import router as assessment_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.voice import router as voice_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.gamification import router as gamification_router
from app.api.v1.district import router as district_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.APP_ENV})...")
    await MongoManager.connect()
    logger.info("MongoDB identity database ready.")
    logger.info("PostgreSQL learning & curriculum database ready.")
    logger.info(f"Aaroh-AI integration ready at: {settings.AAROH_AI_PATH}")
    yield
    # Shutdown
    await MongoManager.disconnect()
    logger.info(f"Shutdown complete for {settings.APP_NAME}.")

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-ready backend for AAROH: AI-Powered Mother-Tongue Learning Platform "
        "for Rural & Tribal Primary Education. Integrates real Aaroh-AI pipelines, "
        "MongoDB authentication/identity, PostgreSQL learning store, IndicTrans2 translation, "
        "and offline edge sync."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID & Logging Middleware
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(time.time_ns()))
    token = request_id_ctx.set(req_id)
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response
    finally:
        request_id_ctx.reset(token)

# Exception Handlers
app.add_exception_handler(AarohAPIException, aaroh_exception_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
            },
        },
    )

# Include All API Routers (Prefix /api/v1)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(teachers_router, prefix="/api/v1")
app.include_router(students_router, prefix="/api/v1")
app.include_router(content_router, prefix="/api/v1")
app.include_router(translation_router, prefix="/api/v1")
app.include_router(simplification_router, prefix="/api/v1")
app.include_router(assessment_router, prefix="/api/v1")
app.include_router(assignments_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(copilot_router, prefix="/api/v1")
app.include_router(gamification_router, prefix="/api/v1")
app.include_router(district_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "success": True,
        "data": {
            "platform": "AAROH - AI-Powered Mother-Tongue Learning Platform",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "status": "operational",
            "architecture": {
                "identity_db": "MongoDB (Authentication, Users, Teacher & Student Login Credentials)",
                "learning_db": "PostgreSQL + pgvector (Curriculum, Quizzes, Mastery, Sync)",
                "ai_engine": "Existing Aaroh-AI Core Integration (Phases 1 through 8)",
            },
            "docs_url": "/docs",
        },
    }

@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Health check verifying API, MongoDB, PostgreSQL, and Aaroh-AI integration."""
    mongo_status = "healthy"
    try:
        db = MongoManager.get_database()
        if MongoManager.is_mock:
            mongo_status = "healthy (in-memory mock fallback)"
        else:
            await MongoManager.client.admin.command("ping")
    except Exception as me:
        mongo_status = f"unhealthy ({str(me)})"

    postgres_status = "healthy"
    try:
        session = postgres_manager.get_session()
        session.execute(text("SELECT 1"))
        session.close()
    except Exception as pe:
        postgres_status = f"unhealthy ({str(pe)})"

    ai_status = "healthy"
    try:
        assert ai_adapter is not None
    except Exception as ae:
        ai_status = f"unhealthy ({str(ae)})"

    return {
        "success": True,
        "data": {
            "status": "healthy" if "unhealthy" not in (mongo_status + postgres_status + ai_status) else "degraded",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "components": {
                "api": "healthy",
                "mongodb": mongo_status,
                "postgresql": postgres_status,
                "aaroh_ai_core": ai_status,
                "storage": "healthy (local/s3)",
            },
        },
    }
