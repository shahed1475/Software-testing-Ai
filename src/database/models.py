"""
SQLAlchemy models for the Testing AI database schema.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum as PyEnum
import uuid

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, 
    ForeignKey, DECIMAL, BIGINT, JSON, ARRAY, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from pydantic import Field as PydanticField

Base = declarative_base()


class TestStatus(PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(PyEnum):
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    SECURITY = "security"
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"


class EnvironmentType(PyEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_name = Column(String(255), nullable=False)
    test_type = Column(Enum(TestType), nullable=False)
    environment = Column(Enum(EnvironmentType), default=EnvironmentType.TESTING)
    status = Column(Enum(TestStatus), default=TestStatus.PENDING)
    start_time = Column(DateTime(timezone=True), default=func.now())
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5, 2))
    branch_name = Column(String(255))
    commit_hash = Column(String(40))
    triggered_by = Column(String(255))
    configuration = Column(JSONB)
    test_metadata = Column(JSONB)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    test_cases = relationship("TestCase", back_populates="test_run", cascade="all, delete-orphan")
    artifacts = relationship("TestArtifact", back_populates="test_run", cascade="all, delete-orphan")
    reports = relationship("TestReport", back_populates="test_run", cascade="all, delete-orphan")

    def calculate_success_rate(self):
        """Calculate and update success rate based on test results."""
        if self.total_tests > 0:
            self.success_rate = round((self.passed_tests / self.total_tests) * 100, 2)
        else:
            self.success_rate = 0.0

    def update_test_counts(self, session: Session):
        """Update test counts based on associated test cases."""
        from sqlalchemy import func
        
        counts = session.query(
            func.count(TestCase.id).label('total'),
            func.count(TestCase.id).filter(TestCase.status == TestStatus.PASSED).label('passed'),
            func.count(TestCase.id).filter(TestCase.status == TestStatus.FAILED).label('failed'),
            func.count(TestCase.id).filter(TestCase.status == TestStatus.SKIPPED).label('skipped'),
            func.count(TestCase.id).filter(TestCase.status == TestStatus.ERROR).label('error')
        ).filter(TestCase.test_run_id == self.id).first()

        self.total_tests = counts.total or 0
        self.passed_tests = counts.passed or 0
        self.failed_tests = counts.failed or 0
        self.skipped_tests = counts.skipped or 0
        self.error_tests = counts.error or 0
        self.calculate_success_rate()


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    test_name = Column(String(500), nullable=False)
    test_file = Column(String(500))
    test_class = Column(String(255))
    test_method = Column(String(255))
    status = Column(Enum(TestStatus), nullable=False)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(DECIMAL(10, 3))
    error_message = Column(Text)
    stack_trace = Column(Text)
    screenshot_path = Column(String(500))
    video_path = Column(String(500))
    logs = Column(Text)
    tags = Column(ARRAY(String))
    test_case_metadata = Column(JSONB)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    test_run = relationship("TestRun", back_populates="test_cases")
    artifacts = relationship("TestArtifact", back_populates="test_case", cascade="all, delete-orphan")


class TestArtifact(Base):
    __tablename__ = "test_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id", ondelete="CASCADE"))
    artifact_type = Column(String(50), nullable=False)  # screenshot, video, log, report, trace
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BIGINT)
    mime_type = Column(String(100))
    storage_location = Column(String(500))  # S3, MinIO, local path
    artifact_metadata = Column(JSONB)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    test_run = relationship("TestRun", back_populates="artifacts")
    test_case = relationship("TestCase", back_populates="artifacts")


class TestEnvironment(Base):
    __tablename__ = "test_environments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(Enum(EnvironmentType), nullable=False)
    base_url = Column(String(500))
    database_url = Column(String(500))
    api_endpoints = Column(JSONB)
    browser_config = Column(JSONB)
    mobile_config = Column(JSONB)
    credentials = Column(JSONB)  # Should be encrypted
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    result_type = Column(String(50), nullable=False)  # assertion, performance, screenshot, etc.
    result_data = Column(JSONB)
    passed = Column(Boolean, nullable=False)
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    test_run = relationship("TestRun")
    test_case = relationship("TestCase")


class TestReport(Base):
    __tablename__ = "test_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(50), nullable=False)  # html, pdf, json, xml
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BIGINT)
    generated_at = Column(DateTime(timezone=True), default=func.now())
    report_metadata = Column(JSONB)  # Renamed from 'metadata' to avoid SQLAlchemy conflict

    # Relationships
    test_run = relationship("TestRun", back_populates="reports")


# Pydantic models for API serialization
class TestRunCreate(BaseModel):
    run_name: str
    test_type: TestType
    environment: EnvironmentType = EnvironmentType.TESTING
    branch_name: Optional[str] = None
    commit_hash: Optional[str] = None
    triggered_by: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TestRunUpdate(BaseModel):
    status: Optional[TestStatus] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_tests: Optional[int] = None
    passed_tests: Optional[int] = None
    failed_tests: Optional[int] = None
    skipped_tests: Optional[int] = None
    error_tests: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TestCaseCreate(BaseModel):
    test_run_id: uuid.UUID
    test_name: str
    test_file: Optional[str] = None
    test_class: Optional[str] = None
    test_method: Optional[str] = None
    status: TestStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    logs: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TestArtifactCreate(BaseModel):
    test_run_id: uuid.UUID
    test_case_id: Optional[uuid.UUID] = None
    artifact_type: str
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    storage_location: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TestEnvironmentCreate(BaseModel):
    name: str
    type: EnvironmentType
    base_url: Optional[str] = None
    database_url: Optional[str] = None
    api_endpoints: Optional[Dict[str, Any]] = None
    browser_config: Optional[Dict[str, Any]] = None
    mobile_config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: bool = True


class TestReportCreate(BaseModel):
    test_run_id: uuid.UUID
    report_type: str
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


# Response models
class TestRunResponse(BaseModel):
    id: uuid.UUID
    run_name: str
    test_type: TestType
    environment: EnvironmentType
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    success_rate: Optional[float]
    branch_name: Optional[str]
    commit_hash: Optional[str]
    triggered_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestCaseResponse(BaseModel):
    id: uuid.UUID
    test_run_id: uuid.UUID
    test_name: str
    test_file: Optional[str]
    test_class: Optional[str]
    test_method: Optional[str]
    status: TestStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True