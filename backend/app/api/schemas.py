"""
# Architect: Meet Kumar
# InsightAI - Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============== User Schemas ==============

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: Union[str, UUID]
    is_active: bool
    is_verified: bool
    subscription_tier: str
    datasets_count: int
    analyses_count: int
    storage_used_bytes: int
    created_at: datetime
    last_login: Optional[datetime]


# ============== Token Schemas ==============

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[datetime] = None


# ============== Dataset Schemas ==============

class DatasetStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DatasetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class DatasetCreate(DatasetBase):
    pass


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Union[str, UUID]
    user_id: Union[str, UUID]
    name: str
    original_filename: str
    file_size: int
    file_size_formatted: str
    row_count: Optional[int]
    column_count: Optional[int]
    status: str
    data_health_score: Optional[float]
    missing_values_count: Optional[int]
    duplicate_rows_count: Optional[int]
    column_schema: Optional[Dict[str, Any]] = None
    cleaning_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]


class DatasetListResponse(BaseModel):
    items: List[DatasetResponse]
    total: int
    page: int
    page_size: int


class DatasetPreviewResponse(BaseModel):
    columns: List[str]
    data: List[Dict[str, Any]]
    total_rows: int
    preview_rows: int


# ============== Analysis Schemas ==============

class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisType(str, Enum):
    CLEANING = "cleaning"
    EXPLORATION = "exploration"
    VISUALIZATION = "visualization"
    CORRELATION = "correlation"
    CUSTOM = "custom"


# ============== Analysis Schemas ==============

class AnalysisResult(BaseModel):
    insights: List[str]
    anomalies: List[str]
    strategy: str


class DataAnalysisResponse(BaseModel):
    metadata: Dict[str, Any]
    ai_insights: AnalysisResult


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: Optional[List[ChatHistoryItem]] = None


class ChatResponse(BaseModel):
    reply: str


class StartAnalysisRequest(BaseModel):
    dataset_id: str
    query: Optional[str] = None
    analysis_type: AnalysisType = AnalysisType.EXPLORATION


class ThoughtItem(BaseModel):
    id: str
    timestamp: str
    type: str  # "thinking", "action", "observation", "result", "error"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Union[str, UUID]
    user_id: Union[str, UUID]
    dataset_id: Union[str, UUID]
    dataset: Optional[DatasetResponse] = None
    query: Optional[str]
    analysis_type: Optional[str]
    status: str
    error_message: Optional[str]
    thought_process: Optional[List[ThoughtItem]] = None
    result_summary: Optional[Dict[str, Any]] = None
    generated_code: Optional[str] = None
    output_files: Optional[List[str]] = None
    insights: Optional[List[Dict[str, Any]]] = None
    duration_seconds: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class AnalysisCreateResponse(BaseModel):
    id: Union[str, UUID]
    status: str
    message: Optional[str] = None


class AnalysisStreamEvent(BaseModel):
    event: str  # "thought", "progress", "result", "error", "complete"
    data: Dict[str, Any]


# ============== Session/History Schemas ==============

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    session_id: Union[str, UUID] = Field(alias="id")
    filename: str
    created_at: datetime


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]


# ============== Pipeline Schemas ==============

class CleaningStep(BaseModel):
    operation: str  # "drop_na", "fill_na", "drop_duplicates", "rename_column", etc.
    params: Dict[str, Any]
    order: int


class PipelineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class PipelineCreate(PipelineBase):
    dataset_id: Optional[str] = None
    steps: List[Dict[str, Any]] = []
    is_template: bool = False


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None


class PipelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    dataset_id: Optional[str]
    name: str
    description: Optional[str]
    steps: List[Dict[str, Any]]
    is_template: bool
    is_public: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime


# ============== Upload Schemas ==============

class UploadResponse(BaseModel):
    task_id: Optional[str] = None
    dataset_id: str
    message: str
    status: str


# ============== Dashboard Schemas ==============

class DashboardStats(BaseModel):
    total_datasets: int
    total_analyses: int
    storage_used_bytes: int
    storage_used_formatted: str
    recent_datasets: List[DatasetResponse]
    recent_analyses: List[AnalysisResponse]
    data_health_average: Optional[float]


# ============== Health Schemas ==============

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]
