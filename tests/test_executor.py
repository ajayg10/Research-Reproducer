"""Tests for Executor agent."""

import pytest
from backend.agents.executor import executor_agent


@pytest.mark.asyncio
async def test_executor_missing_workspace():
    """Test executor with missing workspace."""
    result = await executor_agent.execute(
        input_data={"workspace_path": "/nonexistent"},
        pipeline_id="test-123"
    )

    assert result.success is False
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_executor_no_workspace():
    """Test executor with no workspace path."""
    result = await executor_agent.execute(
        input_data={},
        pipeline_id="test-123"
    )

    assert result.success is False
    assert "No workspace path" in result.error


@pytest.mark.asyncio
@pytest.mark.slow
async def test_executor_simple_script():
    """Test execution of a simple Python script."""
    # This would create a temp workspace with a simple script
    # and verify it executes successfully
    pass
