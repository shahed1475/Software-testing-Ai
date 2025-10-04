"""
Database connection and session management for Testing AI.
"""

import os
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


class DatabaseManager:
    """Database connection and session manager."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager with connection URL."""
        self.database_url = database_url or self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables."""
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "testing_ai")
        db_user = os.getenv("DB_USER", "testuser")
        db_password = os.getenv("DB_PASSWORD", "testpass")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with appropriate configuration."""
        engine_kwargs = {
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
        
        # Handle SQLite for testing
        if self.database_url.startswith("sqlite"):
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False}
            })
        
        engine = create_engine(self.database_url, **engine_kwargs)
        
        # Enable foreign key constraints for SQLite
        if self.database_url.startswith("sqlite"):
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        return engine
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            return True
        except Exception:
            return False


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session for FastAPI."""
    with db_manager.session_scope() as session:
        yield session


def init_database():
    """Initialize database with tables and default data."""
    db_manager.create_tables()
    
    # Insert default test environments if they don't exist
    with db_manager.session_scope() as session:
        from .models import TestEnvironment, EnvironmentType
        
        # Check if environments already exist
        existing_envs = session.query(TestEnvironment).count()
        if existing_envs == 0:
            default_environments = [
                TestEnvironment(
                    name="Local Development",
                    type=EnvironmentType.DEVELOPMENT,
                    base_url="http://localhost:3000",
                    is_active=True
                ),
                TestEnvironment(
                    name="Staging",
                    type=EnvironmentType.STAGING,
                    base_url="https://staging.example.com",
                    is_active=True
                ),
                TestEnvironment(
                    name="Production",
                    type=EnvironmentType.PRODUCTION,
                    base_url="https://example.com",
                    is_active=True
                )
            ]
            
            for env in default_environments:
                session.add(env)


def reset_database():
    """Reset database by dropping and recreating all tables."""
    db_manager.drop_tables()
    init_database()


# Database utilities for testing
class TestDatabaseManager(DatabaseManager):
    """Database manager for testing with in-memory SQLite."""
    
    def __init__(self):
        super().__init__("sqlite:///:memory:")
        self.create_tables()


def get_test_db() -> Generator[Session, None, None]:
    """Get test database session."""
    test_db = TestDatabaseManager()
    with test_db.session_scope() as session:
        yield session


# Alembic configuration helper
def get_alembic_config():
    """Get Alembic configuration for migrations."""
    from alembic.config import Config
    from alembic import command
    
    # Create alembic.ini if it doesn't exist
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "database/migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", db_manager.database_url)
    
    return alembic_cfg


def run_migrations():
    """Run database migrations."""
    try:
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully.")
    except Exception as e:
        print(f"Error running migrations: {e}")
        # Fallback to creating tables directly
        init_database()


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    print("Database initialized successfully.")