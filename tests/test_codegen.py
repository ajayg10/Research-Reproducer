"""Tests for Codegen agent."""

import pytest
from pathlib import Path
from backend.agents.codegen import codegen_agent
from backend.models.schemas import ImplementationPlan


@pytest.mark.asyncio
async def test_codegen_basic_generation():
    """Test basic code generation."""
    plan = ImplementationPlan(
        dependencies=["numpy", "torch"],
        model_implementation={"type": "simple"},
        dataset_pipeline={"name": "test"},
        training_loop={"epochs": 10},
        metrics_to_capture=["accuracy"]
    )

    # This would mock Gemini and check file generation
    pass


@pytest.mark.asyncio
async def test_codegen_file_structure():
    """Test generated file structure is correct."""
    # Verify train.py, model.py, dataset.py, etc. are created
    pass
