"""Pydantic models for pipeline state management."""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    QUEUED = "queued"
    PARSING = "parsing"
    PLANNING = "planning"
    GENERATING = "generating"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RETRYING = "retrying"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class AgentType(str, Enum):
    """Agent types in the system."""
    PARSER = "parser"
    PLANNER = "planner"
    CODEGEN = "codegen"
    EXECUTOR = "executor"
    VERIFIER = "verifier"


class PipelineState(BaseModel):
    """Complete pipeline state."""
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    status: PipelineStatus = Field(default=PipelineStatus.QUEUED)
    paper_source: str = Field(..., description="PDF path or arXiv URL")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Agent outputs
    parser_output: Optional[Dict[str, Any]] = None
    planner_output: Optional[Dict[str, Any]] = None
    codegen_output: Optional[Dict[str, Any]] = None
    executor_output: Optional[Dict[str, Any]] = None
    verifier_output: Optional[Dict[str, Any]] = None

    # Retry tracking
    retry_count: int = Field(default=0)
    retry_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Error tracking
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentExecution(BaseModel):
    """Record of a single agent execution."""
    agent_type: AgentType
    pipeline_id: str
    execution_id: str
    status: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    token_usage: Optional[int] = None
    execution_time_seconds: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
