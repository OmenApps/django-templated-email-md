"""Exceptions for the MarkdownTemplateBackend."""


class MarkdownTemplateBackendError(Exception):
    """Base exception for MarkdownTemplateBackend errors."""


class MarkdownRenderError(MarkdownTemplateBackendError):
    """Raised when Markdown rendering fails."""


class CSSInliningError(MarkdownTemplateBackendError):
    """Raised when CSS inlining fails."""
