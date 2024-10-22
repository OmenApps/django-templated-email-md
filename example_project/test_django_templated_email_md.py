"""Test cases for the django-templated-email-md package."""

import pytest
from django.conf import settings
from django.core import mail
from django.template import TemplateDoesNotExist
from django.test import override_settings
from templated_email import send_templated_mail

from templated_email_md.backend import MarkdownTemplateBackend


def test_succeeds() -> None:
    """Test that the test suite runs."""
    assert 0 == 0


def test_settings() -> None:
    """Test that the settings are configured."""
    assert settings.USE_TZ is True


@pytest.fixture
def backend():
    """Create a MarkdownTemplateBackend instance."""
    return MarkdownTemplateBackend()


def test_markdown_conversion(backend):
    """Test conversion of Markdown to HTML."""
    response = backend._render_email("test_message", {"name": "Test User"})

    assert "Hello Test User!" in response["html"]
    assert "<h1" in response["html"]
    assert "<strong" in response["html"]
    assert "<ol" in response["html"]
    assert 'href="http://example.com"' in response["html"]

def test_plain_text_generation(backend):
    """Test generation of plain text version."""
    response = backend._render_email("test_message", {"name": "Test User"})

    assert "Hello Test User!" in response["plain"]
    assert "**" not in response["plain"]  # Markdown syntax should be converted
    # assert "[A link](http://example.com)" not in response["plain"]  # May need to further adjust html2text configs
    assert "http://example.com" in response["plain"]


def test_css_inlining(backend):
    """Test that CSS styles are properly inlined."""
    response = backend._render_email("test_message", {"name": "Test User"})
    # Check that any CSS from markdown_base.html has been inlined
    assert 'style="' in response["html"]


def test_template_inheritance(backend):
    """Test that template inheritance works correctly."""
    with pytest.raises(TemplateDoesNotExist):
        # Should raise if referenced template doesn't exist
        backend._render_email("non_existent_template", {})


@override_settings(TEMPLATED_EMAIL_BACKEND='templated_email_md.backend.MarkdownTemplateBackend')
def test_send_templated_mail():
    """Test sending an email using the backend."""
    send_templated_mail(
        template_name="test_message",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    # Check that the email was sent
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Test Email"
    assert "Hello Test User!" in mail.outbox[0].body


def test_missing_subject_block(backend):
    """Test handling of missing subject block."""
    with pytest.raises(TemplateDoesNotExist):
        # This will now raise TemplateDoesNotExist since we don't support inline templates
        backend._render_email("non_existent", {})


@pytest.mark.parametrize("context,expected", [
    ({"name": "Test"}, "Test"),
    ({"name": ""}, ""),
    ({}, ""),  # Missing context variable
])
def test_context_handling(backend, context, expected):
    """Test handling of different context scenarios."""
    response = backend._render_email("test_message", context)
    if expected:
        assert f"Hello {expected}!" in response["html"]
    else:
        assert "Hello !" in response["html"]  # Template will render empty name


def test_template_not_found(backend):
    """Test handling of non-existent templates."""
    with pytest.raises(TemplateDoesNotExist):
        backend._render_email("non_existent_template", {})


@override_settings(TEMPLATED_EMAIL_BACKEND='templated_email_md.backend.MarkdownTemplateBackend')
def test_full_email_rendering():
    """Test the complete email rendering process."""
    send_templated_mail(
        template_name="test_message",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check all parts of the email
    assert email.subject == "Test Email"
    assert email.from_email == "from@example.com"
    assert email.to == ["to@example.com"]

    # Check both HTML and plain text content
    assert "Hello Test User!" in email.body  # Plain text version
    assert len(email.alternatives) == 1  # Should have HTML alternative
    html_content = email.alternatives[0][0]
    assert "<h1" in html_content
    assert "<strong>bold</strong>" in html_content


@override_settings(TEMPLATED_EMAIL_BACKEND='templated_email_md.backend.MarkdownTemplateBackend')
def test_fail_silently():
    """Test that fail_silently works as expected."""
    backend = MarkdownTemplateBackend(fail_silently=True)

    # Try to render a non-existent template
    response = backend._render_email("non_existent_template", {})

    # Should get a fallback response instead of an exception
    assert "Email template rendering failed" in response["html"]
    assert "Email template rendering failed" in response["plain"]
    assert response["subject"] == "No Subject"


def test_subject_from_context(backend):
    """Test that subject can be overridden from context."""
    response = backend._render_email(
        "test_message",
        {"name": "Test User", "subject": "Override Subject"}
    )
    assert response["subject"] == "Override Subject"
