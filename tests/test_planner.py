"""Tests for Planner agent."""

import pytest
from backend.agents.planner import planner_agent
from backend.models.schemas import PaperSpecification


@pytest.mark.asyncio
async def test_planner_basic_plan():
    """Test basic planning functionality."""
    spec = PaperSpecification(
        title="Test Paper",
        problem_definition="Classification task",
        architecture={"type": "neural_network", "layers": [10, 5, 2]},
        hyperparameters={"lr": 0.001, "batch_size": 32, "epochs": 10},
        dataset={"name": "iris"},
        claimed_results=[{"metric": "accuracy", "value": 0.95}]
    )

    # This would require mocking Gemini client
    # For full test, inject mock
    pass


@pytest.mark.asyncio
async def test_planner_minimal_spec():
    """Test planner with minimal specification."""
    spec = PaperSpecification(
        title="Minimal Paper",
        problem_definition="Test"
    )

    # Should still generate a plan, even if sparse
    pass
