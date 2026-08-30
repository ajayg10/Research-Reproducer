"""Pytest configuration."""

import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


@pytest.fixture
def mock_gemini_client(monkeypatch):
    """Mock Gemini client for testing."""
    # TODO: Implement mock
    pass


@pytest.fixture
def mock_pdf_processor(monkeypatch):
    """Mock PDF processor for testing."""
    # TODO: Implement mock
    pass


@pytest.fixture
def mock_docker_client(monkeypatch):
    """Mock Docker client for testing."""
    # TODO: Implement mock
    pass
