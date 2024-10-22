"""Pytest fixtures for templated_email_md tests."""

import pytest

from templated_email_md.backend import MarkdownTemplateBackend


@pytest.fixture
def backend():
    """Create a MarkdownTemplateBackend instance."""
    return MarkdownTemplateBackend()
