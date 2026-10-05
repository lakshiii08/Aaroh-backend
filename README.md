# AAROH — AI-Powered Mother-Tongue Learning Platform: Backend & Aaroh-AI Integration

A production-ready, dual-database **FastAPI** backend for **AAROH**, an AI-powered mother-tongue learning platform tailored for rural and tribal primary education.

This backend interfaces directly with the existing **Aaroh-AI** pipeline engine (located at `../Aaroh-AI` or specified via `AAROH_AI_PATH`), providing real Indic translation, speech synthesis/recognition, concept extraction, RAG vector retrieval, LangGraph agents, quiz generation, automated remediation, teacher copilots, and offline edge synchronization.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI REST API Gateway                        │
│             (/api/v1: Auth, Teachers, Students, Content, AI)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
        ┌───────────────────┐               ┌───────────────────┐
        │   MongoDB Engine  │               │ PostgreSQL Engine │
        │   (Identity &     │               │   (Curriculum &   │
        │  Authentication)  │               │  Learning Data)   │
        └───────────────────┘               └───────────────────┘
                  │                                   │
                  │                                   ▼
                  │                         ┌───────────────────┐
                  │                         │  Aaroh-AI Adapter │
                  │                         │       Layer       │
                  │                         └─────────┬─────────┘
                  │                                   │
                  │                                   ▼
                  │                         ┌───────────────────┐
                  │                         │ Existing Aaroh-AI │
                  │                         │ Pipeline (Phases  │
                  │                         │   1 through 8)    │
                  └─────────────────────────┴───────────────────┘
```

---

## 💾 Dual Database Responsibility Separation

To guarantee data isolation, high-speed authentication, and structured educational analytics, AAROH strictly separates responsibilities across two databases:

| Database | Primary Responsibilities | Data Handled |
| :--- | :--- | :--- |
| **MongoDB** | **Identity, Authentication & Credential Management** | Users, Teachers, Admins, District Admins, Parents, Student Credentials, School Identity, Login Sessions, Refresh Tokens, Scoped Roll Numbers. Passwords strictly hashed via `bcrypt`. |
| **PostgreSQL (+ pgvector)** | **Curriculum, Educational Data & AI Engine** | Documents, Text Chunks, Concepts, Learning Outcomes, Vector Embeddings, Translations, Glossaries, Quizzes, Questions, Submissions, Gap Analysis, Remedial Pathways, Voice Lessons, Flashcards, Quests, Offline Bundles, Edge Sync Logs. |

*(Note: In local development or resource-constrained environments, the backend includes automatic fallback to `mongomock-motor` for in-memory MongoDB and pre-populated SQLite `data/aaroh_local.db` for zero-downtime bootstrapping).*

---

## 🎓 Student Login & Teacher Management Flow

Students **never self-register**; teachers onboard students directly from the teacher dashboard.

1. **Teacher Creates Student**:
   - Inputs: `Name`, `Grade/Class`, `Roll Number`, `School ID`, `Village`, `Section`.
2. **Backend Password & Scoped Identity Generation**:
   - Validates uniqueness using scoped identity: `(school_id, roll_number)` to prevent cross-school roll number collision.
   - Generates an 8-character cryptographically secure random password (`secrets.choice` across upper, lower, digits).
   - Hashes the password with `bcrypt`.
   - Stores credential identity in MongoDB (`students` collection).
   - Generates the linked learning profile in PostgreSQL (`students` table).
3. **One-Time Credential Delivery**:
   - Returns the generated password **once** in the teacher's creation response.
   - Credentials:
     - **Login ID**: Student Roll Number (e.g. `27`)
     - **School Code / ID**: School Identifier (e.g. `SCH_BASTAR_01`)
     - **Password**: One-time generated secure password (e.g. `kP9mQ2X7`)
   - The plain password is never stored or returned by any subsequent API endpoint.

---

## 🧠 Aaroh-AI Core Integration (Zero Fake AI)

The backend interacts with the real `Aaroh-AI` code engine via `app.ai.aaroh_ai_adapter.AarohAIAdapter` and specialized sub-adapters:

1. **Content Understanding & Ingestion (`app/ai/content_ai.py`)**:
   - Integrates `src.pipeline.content_pipeline.ContentPipeline`.
   - Document chunking, concept extraction, learning outcome identification, difficulty estimation, and vector embeddings search.
2. **Indic Translation & Dialects (`app/ai/translation_ai.py`)**:
   - Integrates `src.pipeline.translation_pipeline.TranslationPipeline`.
   - Direct IndicTrans2 translation, glossary alignment, and dialect adaptation (Gondi, Halbi, Kudukh, Sadri).
3. **Simplification & LangGraph Agent (`app/ai/simplification_ai.py`)**:
   - Integrates `src.agents.simplification_graph.SimplificationLocalizationGraph`.
   - Age-appropriate localized analogies, cultural storytelling, folk metaphors, and localized village activities.
4. **Assessment & Diagnostic Engine (`app/ai/assessment_ai.py`)**:
   - Integrates `src.pipeline.quiz_pipeline.QuizPipeline`.
   - Concept-aligned question generation, multi-tier Bloom taxonomy evaluation, automated scoring, and student misconception gap analysis.
5. **Voice Intelligence (`app/ai/voice_ai.py`)**:
   - Integrates `src.speech.tts_engine.TTSEngine` and `src.speech.stt_engine.STTEngine`.
   - Edge-friendly speech synthesis with local playback and Indic voice lesson generation.
6. **Teacher Copilot & Offline Edge Sync (`app/ai/copilot_ai.py`)**:
   - Integrates `src.agents.copilot_agent.TeacherCopilotAgent` and `src.offline.edge_packager.EdgePackager`.
   - Multigrade classroom lesson planning, printable remedial activity sheets, offline ZIP bundle compilation, and delta sync processing.

---

## 🚀 API Endpoint Reference

All endpoints are versioned under `/api/v1`.

### 1. Authentication & Identity (`/api/v1/auth`)
- `POST /api/v1/auth/signup` — Teacher / Admin / District Admin registration.
- `POST /api/v1/auth/login` — General email/username login.
- `POST /api/v1/auth/student-login` — Student roll number + school ID authentication.
- `GET /api/v1/auth/me` — Current authenticated user profile.
- `POST /api/v1/auth/refresh` — Refresh access token.
- `POST /api/v1/auth/logout` — Invalidate session.

### 2. Teacher Management (`/api/v1/teachers`)
- `POST /api/v1/teachers/students` — Create new student, returns secure credentials once.
- `GET /api/v1/teachers/students` — List students assigned to teacher's school/grade.
- `GET /api/v1/teachers/students/{student_id}` — View student educational profile.
- `GET /api/v1/teachers/analytics` — Class mastery breakdown and learning gaps.

### 3. Student Learning (`/api/v1/students`)
- `GET /api/v1/students/me` — Authenticated student profile.
- `GET /api/v1/students/lessons` — Assigned localized lessons.
- `GET /api/v1/students/progress` — Personal concept mastery and stats.

### 4. Content Ingestion & Curriculum (`/api/v1/content`)
- `POST /api/v1/content/upload` — Ingest textbook PDF/Image/Text with OCR and concept extraction.
- `GET /api/v1/content/documents` — List ingested documents.
- `GET /api/v1/content/documents/{doc_id}/concepts` — Extracted concepts and outcomes.
- `POST /api/v1/content/search` — Semantic vector search across curriculum chunks.

### 5. Indic Mother-Tongue Translation (`/api/v1/translation`)
- `POST /api/v1/translation/translate` — Translate single text with dialect adaptation.
- `POST /api/v1/translation/batch` — Batch translation.
- `GET /api/v1/translation/languages` — Supported Indic languages & tribal dialects.
- `GET /api/v1/translation/glossary/lookup` — Cultural pedagogical glossary lookup.
- `POST /api/v1/translation/glossary/term` — Register new dialect term.
- `POST /api/v1/translation/lessons/{doc_id}` — Translate entire lesson document.

### 6. Simplification & LangGraph (`/api/v1/simplification`)
- `POST /api/v1/simplification/concepts/{code}` — Localize and simplify concept with rural analogies.
- `POST /api/v1/simplification/documents/{doc_id}` — Simplify complete document.
- `POST /api/v1/simplification/langgraph/concepts/{code}` — Execute multi-agent LangGraph localization.
- `GET /api/v1/simplification/cache/status` — Inspection of pre-computed lesson caches.

### 7. Assessment & Quizzes (`/api/v1/assessment`)
- `POST /api/v1/assessment/quizzes/generate` — Generate concept-aligned Bloom taxonomy quiz.
- `GET /api/v1/assessment/quizzes/{quiz_id}` — Fetch quiz details.
- `POST /api/v1/assessment/quizzes/{quiz_id}/submit` — Submit answers, score, and diagnose gaps.
- `GET /api/v1/assessment/students/{student_id}/history` — Quiz submission history.
- `GET /api/v1/assessment/teachers/reports/{concept_code}` — Class-wide concept diagnostic report.

### 8. Voice Intelligence (`/api/v1/voice`)
- `POST /api/v1/voice/synthesize` — Indic TTS speech synthesis.
- `POST /api/v1/voice/transcribe` — Indic STT audio speech-to-text.
- `POST /api/v1/voice/lessons/{concept_code}` — Generate full multi-segment voice lesson.

### 9. Teacher Copilot & Offline Edge Sync (`/api/v1/copilot`)
- `POST /api/v1/copilot/lesson-plans/generate` — Multigrade lesson plan with blackboard layouts.
- `POST /api/v1/copilot/remedial-aid/generate` — Printable remedial intervention guide.
- `POST /api/v1/copilot/edge/packages/export` — Bundle offline ZIP package for village edge devices.
- `POST /api/v1/copilot/edge/sync` — Ingest offline SQLite delta sync events.
- `GET /api/v1/copilot/analytics/mastery-heatmap` — Multigrade concept mastery heatmap.

### 10. Gamification & Visual Storytelling (`/api/v1/gamification`)
- `POST /api/v1/gamification/quests/generate` — Interactive cultural quest with XP and badges.
- `POST /api/v1/gamification/students/{student_id}/activity` — Log activity and award XP.
- `GET /api/v1/gamification/students/{student_id}/portfolio` — Student badges, XP, and streak.
- `POST /api/v1/gamification/flashcards/generate` — Visual flashcards with image prompts.
- `GET /api/v1/gamification/leaderboards/{school_id}` — Village/school weekly leaderboard.

### 11. District Administration & Interventions (`/api/v1/district`)
- `GET /api/v1/district/analytics/overview` — High-level district mastery, schools, and at-risk count.
- `GET /api/v1/district/interventions/pending` — Flagged low-performing students needing intervention.
- `POST /api/v1/district/interventions/generate-pathway` — 4-step personalized remedial roadmap.
- `POST /api/v1/district/parent-advisory/send-voice-note` — Mother-tongue IVR audio advisory dispatch.

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.10 - 3.14)
- MongoDB instance (or rely on automated in-memory mock fallback)
- PostgreSQL with pgvector extension (or rely on pre-populated local SQLite fallback)

### 1. Installation
Navigate to the `backend` folder and install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Key environment settings:
```ini
APP_NAME=AAROH Backend API
APP_ENV=development
SECRET_KEY=aaroh-super-secret-key-change-in-production-2026

# Databases
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=aaroh_identity_db
POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/aaroh_learning_db

# Aaroh-AI Core Location
AAROH_AI_PATH=../Aaroh-AI
```

### 3. Database Seeding
Seed demo schools, administrators, teachers, and student profiles:

```bash
python scripts/seed_data.py
```

This creates:
- **School**: Government Primary School Bastar (`SCH_BASTAR_01`)
- **Admin**: `admin@aaroh.gov.in` (Password: `AarohAdmin2026!`)
- **District Admin**: `district.admin@aaroh.gov.in` (Password: `DistrictAdmin2026!`)
- **Teacher**: `sarita.devi@aaroh.gov.in` (Password: `TeacherBastar2026!`)
- **Student**: Roll Number `27`, Name: Rahul Murmu (Password: `Murmu@2026`)

### 4. Running the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

### 5. Running Tests

Execute the comprehensive automated test suite:

```bash
# Run all backend tests
pytest tests -v

# Run individual test domains
pytest tests/test_auth.py -v
pytest tests/test_students.py -v
pytest tests/test_security_isolation.py -v
pytest tests/test_ai_endpoints.py -v
```

---

## 🐳 Docker Deployment

To launch the full dual-database ecosystem with PostgreSQL + pgvector and MongoDB:

```bash
docker compose up -d --build
```
#   A a r o h - b a c k e n d  
 