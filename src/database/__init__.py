"""
Database package for Testing AI.
"""

from .database import (
    DatabaseManager,
    db_manager,
    get_db,
    init_database,
    reset_database,
    TestDatabaseManager,
    get_test_db,
    run_migrations
)

from .models import (
    Base,
    TestRun,
    TestCase,
    TestArtifact,
    TestEnvironment,
    TestReport,
    TestStatus,
    TestType,
    EnvironmentType,
    TestRunCreate,
    TestRunUpdate,
    TestCaseCreate,
    TestArtifactCreate,
    TestEnvironmentCreate,
    TestReportCreate,
    TestRunResponse,
    TestCaseResponse
)

__all__ = [
    # Database management
    "DatabaseManager",
    "db_manager",
    "get_db",
    "init_database",
    "reset_database",
    "TestDatabaseManager",
    "get_test_db",
    "run_migrations",
    
    # Models
    "Base",
    "TestRun",
    "TestCase",
    "TestArtifact",
    "TestEnvironment",
    "TestReport",
    
    # Enums
    "TestStatus",
    "TestType",
    "EnvironmentType",
    
    # Pydantic models
    "TestRunCreate",
    "TestRunUpdate",
    "TestCaseCreate",
    "TestArtifactCreate",
    "TestEnvironmentCreate",
    "TestReportCreate",
    "TestRunResponse",
    "TestCaseResponse"
]