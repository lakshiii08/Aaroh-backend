# AAROH Database Architecture & Migrations

AAROH uses a strict dual-database architecture:

## 1. MongoDB (Authentication & Identity)
- **Database**: `aaroh_auth_db`
- **Collections**:
  - `users`: Identity documents, hashed passwords, roles (`ADMIN`, `DISTRICT_ADMIN`, `TEACHER`, `STUDENT`, `PARENT`).
  - `students`: Student identity, roll numbers, school context, grade levels, sections.
  - `teachers`: Teacher identity, school ID, district ID, assigned grades, subjects.
  - `schools`: School codes, names, villages, districts.
  - `sessions`: Active JWT sessions and revocation status.
- **Indexes**:
  - `users.email` (unique, sparse)
  - `users.user_id` (unique)
  - `students`: Compound unique index on `(school_id, grade_level, roll_number)`
  - `schools.school_id` (unique)
  - `sessions.token_jti` (unique)

## 2. PostgreSQL + pgvector (Learning, Content & Analytics)
- **Database**: `aaroh_learning_db`
- **Tables**:
  - `raw_documents`: Uploaded curriculum files, statuses, metadata.
  - `concepts`: Extracted atomic concepts, Bloom's taxonomy, rural context anchors.
  - `content_chunks`: Text chunks with 1536-dimensional Titan vector embeddings (`pgvector`).
  - `quizzes`: Formative quizzes with pedagogical Bloom's mapping.
  - `quiz_submissions`: Student attempt scores and response logs.
  - `assessment_results`: Bayesian knowledge gap analysis and remedial triggers.
  - `voice_lessons`: Synthesized mother-tongue audio tracks.
  - `oral_quiz_attempts`: Audio responses and STT scoring.
  - `lesson_plans`: Multigrade single-teacher lesson plans.
  - `offline_packages`: Edge offline sync zip bundles.
  - `edge_sync_logs`: Edge tablet sync audit logs.
  - `student_profiles`: XP, levels, learning streaks, concept mastery.
  - `student_badges`: Unlocked badges and achievements.
  - `learning_quests`: Village nature observation micro-challenges.
  - `visual_flashcards`: Multilingual flashcards with tribal dialect terms.
  - `intervention_pathways`: 4-step personalized remedial pathways.
  - `parent_voice_advisories`: Dispatched audio notes for non-literate parents.
  - `district_schools`: District administrative school registry.

## Initialization
Schemas are automatically verified and initialized upon server startup via `app.core.mongodb.MongoManager` and `app.core.postgres.PostgresDatabaseManager`. For production migrations, standard Alembic scripts can target the SQLAlchemy metadata in `app.models.pg_models.Base.metadata`.
