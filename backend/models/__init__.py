"""Models package initialization."""

from backend.models.schemas import (
    PaperSpecification,
    ParserOutput,
    ImplementationPlan,
    PlannerOutput,
    GeneratedImplementation,
    CodegenOutput,
    ExecutionResult,
    ExecutorOutput,
    VerificationReport,
    VerifierOutput,
    ReproductionRequest,
    ReproductionResponse,
    PipelineStatusResponse,
    MetricComparison,
    DiscrepancyCategory,
    ReproducibilityVerdict,
)

from backend.models.state import (
    PipelineStatus,
    PipelineState,
    AgentType,
    AgentExecution,
)

__all__ = [
    # Schemas
    "PaperSpecification",
    "ParserOutput",
    "ImplementationPlan",
    "PlannerOutput",
    "GeneratedImplementation",
    "CodegenOutput",
    "ExecutionResult",
    "ExecutorOutput",
    "VerificationReport",
    "VerifierOutput",
    "ReproductionRequest",
    "ReproductionResponse",
    "PipelineStatusResponse",
    "MetricComparison",
    "DiscrepancyCategory",
    "ReproducibilityVerdict",
    # State
    "PipelineStatus",
    "PipelineState",
    "AgentType",
    "AgentExecution",
]
