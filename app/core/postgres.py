import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.logging import logger

# Import Base and models from Aaroh-AI's comprehensive database definition
try:
    from src.aaroh.database.models import Base
    from src.aaroh.database.session import DatabaseManager as AarohDatabaseManager
except ImportError:
    # If path hasn't loaded yet, try adding
    import sys
    sys.path.insert(0, settings.AAROH_AI_PATH)
    sys.path.insert(0, str(Path(settings.AAROH_AI_PATH) / "src"))
    from src.aaroh.database.models import Base
    from src.aaroh.database.session import DatabaseManager as AarohDatabaseManager

class PostgresDatabaseManager:
    def __init__(self):
        self.engine = self._create_engine()
        self.SessionFactory = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self._init_db()

    def _create_engine(self):
        """Creates SQLAlchemy engine with PostgreSQL or SQLite fallback."""
        url = settings.DATABASE_URL
        if not url:
            if not settings.USE_SQLITE_FALLBACK:
                url = (
                    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
                    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
                )

        if url and "postgresql" in url:
            try:
                engine = create_engine(url, pool_size=10, max_overflow=20, echo=False)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Connected successfully to PostgreSQL database: {url.split('@')[-1]}")
                return engine
            except Exception as e:
                if not settings.USE_SQLITE_FALLBACK:
                    logger.error("PostgreSQL connection failed and SQLite fallback is disabled.")
                    raise
                logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite database.")
        elif not settings.USE_SQLITE_FALLBACK:
            raise RuntimeError("DATABASE_URL or complete PostgreSQL settings are required when SQLite fallback is disabled.")

        # SQLite Fallback for local development and test isolation
        db_path = Path(settings.SQLITE_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_url = f"sqlite:///{db_path}"
        engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})
        logger.info(f"Using SQLite database for curriculum and learning data at: {sqlite_url}")
        return engine

    def _init_db(self):
        """Initializes tables and pgvector extension if PostgreSQL."""
        try:
            if "postgresql" in str(self.engine.url):
                with self.engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
            # Ensure all extended models are registered on Base
            import app.models.pg_models  # noqa: F401
            Base.metadata.create_all(bind=self.engine)
            logger.info("PostgreSQL schema initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database schema: {e}")

    def get_session(self) -> Session:
        return self.SessionFactory()

postgres_manager = PostgresDatabaseManager()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for injecting database session into route handlers."""
    session = postgres_manager.get_session()
    try:
        yield session
    finally:
        session.close()
