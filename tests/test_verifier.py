"""Tests for Verifier agent."""

import pytest
from backend.agents.verifier import verifier_agent
from backend.models.schemas import PaperSpecification, ExecutionResult, ReproducibilityVerdict


@pytest.mark.asyncio
async def test_verifier_successful_reproduction():
    """Test verifier with matching metrics."""
    spec = PaperSpecification(
        title="Test",
        claimed_results=[{"metric": "accuracy", "value": 0.95}]
    )

    exec_result = ExecutionResult(
        status="success",
        exit_code=0,
        runtime_seconds=10.0,
        metrics={"accuracy": 0.95}
    )

    result = await verifier_agent.execute(
        input_data={
            "specification": spec.model_dump(),
            "execution_result": exec_result.model_dump()
        },
        pipeline_id="test-123"
    )

    assert result.success is True
    assert result.report.verdict == ReproducibilityVerdict.SUCCESSFUL


@pytest.mark.asyncio
async def test_verifier_failed_execution():
    """Test verifier with failed execution."""
    spec = PaperSpecification(
        title="Test",
        claimed_results=[{"metric": "accuracy", "value": 0.95}]
    )

    exec_result = ExecutionResult(
        status="failure",
        exit_code=1,
        runtime_seconds=5.0,
        error="Execution failed"
    )

    result = await verifier_agent.execute(
        input_data={
            "specification": spec.model_dump(),
            "execution_result": exec_result.model_dump()
        },
        pipeline_id="test-123"
    )

    assert result.success is True
    assert result.report.verdict == ReproducibilityVerdict.EXECUTION_FAILED


@pytest.mark.asyncio
async def test_verifier_partial_reproduction():
    """Test verifier with some metrics passing."""
    spec = PaperSpecification(
        title="Test",
        claimed_results=[
            {"metric": "accuracy", "value": 0.95},
            {"metric": "f1", "value": 0.92}
        ]
    )

    exec_result = ExecutionResult(
        status="success",
        exit_code=0,
        runtime_seconds=10.0,
        metrics={
            "accuracy": 0.95,  # Matches
            "f1": 0.80  # Doesn't match (> 2% diff)
        }
    )

    result = await verifier_agent.execute(
        input_data={
            "specification": spec.model_dump(),
            "execution_result": exec_result.model_dump()
        },
        pipeline_id="test-123"
    )

    assert result.success is True
    assert result.report.verdict == ReproducibilityVerdict.PARTIAL
