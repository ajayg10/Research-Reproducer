"""Tests for Parser agent."""

import pytest
from backend.agents.parser import parser_agent
from backend.models.schemas import PaperSpecification


@pytest.mark.asyncio
async def test_parser_basic_extraction():
    """Test basic paper parsing."""
    # This would require a real PDF file
    # For unit test, we'd mock the PDF processor and Gemini client
    pass


@pytest.mark.asyncio
async def test_parser_missing_file():
    """Test parser with missing PDF file."""
    result = await parser_agent.execute(
        input_data={"paper_source": "/nonexistent.pdf"},
        pipeline_id="test-123"
    )

    assert result.success is False
    assert "Failed to extract text" in result.error


@pytest.mark.asyncio
async def test_parser_no_source():
    """Test parser with no paper source."""
    result = await parser_agent.execute(
        input_data={},
        pipeline_id="test-123"
    )

    assert result.success is False
    assert "No paper source provided" in result.error
