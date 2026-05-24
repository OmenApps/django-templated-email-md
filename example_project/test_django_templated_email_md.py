"""Test cases for the django-templated-email-md package."""

import html as html_stdlib
import io
import os

import pytest
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.template import TemplateDoesNotExist
from django.utils import translation
from django.utils.translation import gettext as _
from templated_email import send_templated_mail

from example_project.example.views import index
from example_project.urls import urlpatterns
from templated_email_md.backend import MarkdownTemplateBackend


def test_succeeds() -> None:
    """Test that the test suite runs."""
    assert 0 == 0


def test_settings() -> None:
    """Test that the settings are configured."""
    assert settings.USE_TZ is True


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
    assert "http://example.com" in response["plain"]


def test_css_inlining(backend):
    """Test that CSS styles are properly inlined."""
    response = backend._render_email("test_message", {"name": "Test User"})
    # Check that any CSS from markdown_base.html has been inlined
    assert 'style="' in response["html"]


def test_template_missing(backend):
    """Test that missing templates raise an exception."""
    with pytest.raises(TemplateDoesNotExist):
        # Should raise if referenced template doesn't exist
        backend._render_email("non_existent_template", {})


def test_send_templated_mail():
    """Test sending an email using the backend."""
    settings.TEMPLATED_EMAIL_BACKEND = "templated_email_md.backend.MarkdownTemplateBackend"
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


@pytest.mark.parametrize(
    "context,expected",
    [
        ({"name": "Test"}, "Test"),
        ({"name": ""}, ""),
        ({}, ""),  # Missing context variable
    ],
)
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


def test_full_email_rendering():
    """Test the complete email rendering process."""
    settings.TEMPLATED_EMAIL_BACKEND = "templated_email_md.backend.MarkdownTemplateBackend"
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


def test_fail_silently():
    """Test that fail_silently works as expected."""
    settings.TEMPLATED_EMAIL_BACKEND = "templated_email_md.backend.MarkdownTemplateBackend"
    backend = MarkdownTemplateBackend(fail_silently=True)

    # Try to render a non-existent template
    response = backend._render_email("non_existent_template", {})

    # Should get a fallback response instead of an exception
    assert "Email template rendering failed" in response["html"]
    assert "Email template rendering failed" in response["plain"]
    assert response["subject"] == "Hello!"


def test_subject_from_context(backend):
    """Test that subject can be overridden from context."""
    response = backend._render_email("test_message", {"name": "Test User", "subject": "Override Subject"})
    assert response["subject"] == "Override Subject"


def test_subject_in_context():
    """Test that providing 'subject' in context overrides the template subject."""
    send_templated_mail(
        template_name="test_message",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User", "subject": "Subject from Context"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    assert email.subject == "Subject from Context"


def test_subject_from_template():
    """Test that the subject defined in the template is used."""
    send_templated_mail(
        template_name="test_subject_block",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    assert email.subject == "Subject from Template"


def test_email_translation():
    """Test that the email is translated according to the active language."""
    with translation.override("es"):
        send_templated_mail(
            template_name="test_translation",
            from_email="from@example.com",
            recipient_list=["to@example.com"],
            context={"name": "Test User"},
        )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check that the email subject and body are in Spanish
    assert email.subject == "Correo electrónico de prueba"
    assert "Hola Test User!" in email.body


def test_override_html2text_settings():
    """Test that overriding html2text settings affects plain text output."""
    settings.TEMPLATED_EMAIL_HTML2TEXT_SETTINGS = {"ignore_links": True}
    send_templated_mail(
        template_name="test_message_with_link",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check that the link is not in the plain text version
    assert "http://example.com" not in email.body
    # Ensure the link is still in the HTML version
    html_content = email.alternatives[0][0]
    assert "http://example.com" in html_content


def test_template_inheritance():
    """Test that template inheritance works correctly."""
    send_templated_mail(
        template_name="child_email",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    assert email.subject == "Child Email Subject"
    assert "Child Email Content" in email.body


def test_template_name_list():
    """Test that providing a list of template names works."""
    send_templated_mail(
        template_name=["test_message", "test_message"],
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Should have used 'test_message' template
    assert "Hello Test User!" in email.body


def test_markdown_extensions(settings):
    """Test that custom markdown extensions are applied."""
    settings.TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS = ["markdown.extensions.tables"]

    send_templated_mail(
        template_name="test_markdown_table",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    html_content = email.alternatives[0][0]

    # Check that the table is rendered correctly in HTML
    assert "<table" in html_content
    assert "Header 1</th>" in html_content


def test_large_email_content():
    """Test that large email content is handled correctly."""

    send_templated_mail(
        template_name="test_large_content",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    assert "This is a line." in email.body


def test_unusual_markdown_features():
    """Test that unusual markdown features are handled correctly."""
    settings.TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS = ["markdown.extensions.footnotes"]
    send_templated_mail(
        template_name="test_unusual_markdown",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    html_content = email.alternatives[0][0]

    # Check that footnotes are rendered if the extension is enabled
    assert "footnote-backref" in html_content


def test_empty_context():
    """Test sending an email with an empty context."""
    send_templated_mail(
        template_name="test_message",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={},  # Empty context
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Ensure that default values or empty strings are used for variables
    assert "Hello" in email.body


def test_preheader_from_template():
    """Test that the preheader defined in the template is included in the email."""
    send_templated_mail(
        template_name="test_preheader_block",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check that preheader is in the HTML alternative email body, but not plain text
    assert "Preheader from Template" in email.alternatives[0][0]


def test_preheader_in_context():
    """Test that providing 'preheader' in context adds it to the email."""
    send_templated_mail(
        template_name="test_message",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User", "preheader": "Preheader from Context"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check that preheader is in the HTML alternative email body, but not plain text
    assert "Preheader from Context" in email.alternatives[0][0]


def test_remove_comments():
    """Test that HTML and JavaScript comments are removed from the HTML content."""
    backend = MarkdownTemplateBackend()
    html_with_comments = """
    <div>
        <!-- HTML Comment -->
        <style>
            /* CSS Comment */
            .class { color: red; }
        </style>
        <script>
            /* JavaScript Comment */
            // This is also a comment
            var url = "http://example.com";
            var relativeUrl = "//cdn.example.com";
            /* Multi-line
            Comment */
            var x = 1; // End of line comment
        </script>
        <a href="http://example.com">Link</a>
        <img src="//cdn.example.com/image.jpg">
        <!--[if IE]>IE specific content<![endif]-->
    </div>
    <div>Content</div>
    """
    cleaned_html = backend._remove_comments(html_with_comments)  # pylint: disable=W0212

    # Regular comments should be removed
    assert "HTML Comment" not in cleaned_html
    assert "Another Comment" not in cleaned_html
    assert "CSS Comment" not in cleaned_html
    assert "JavaScript Comment" not in cleaned_html
    assert "/* Multi-line" not in cleaned_html
    assert "Comment */" not in cleaned_html
    assert "End of line comment" not in cleaned_html
    assert "This is also a comment" not in cleaned_html
    assert "/*" not in cleaned_html
    assert "*/" not in cleaned_html

    # Content should remain
    assert "<div>Content</div>" in cleaned_html
    assert ".class { color: red; }" in cleaned_html
    assert "var x = 1;" in cleaned_html
    assert "Link" in cleaned_html
    assert "//cdn.example.com" in cleaned_html

    # IE conditional comments should be preserved
    assert "<!--[if IE]>IE specific content<![endif]-->" in cleaned_html


def test_default_subject_and_preheader():
    """
    Test that the default subject and preheader are used when
    not provided in the template or context.
    """
    # Send an email without subject or preheader in template or context
    send_templated_mail(
        template_name="test_no_subject_preheader",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Default subject should be 'Hello!' as per the default in the backend
    assert email.subject == _("Hello!")
    # Preheader should be empty string by default
    # Since preheader may not be directly visible, check in the HTML content
    html_content = email.alternatives[0][0]
    assert "Hello!" in email.subject
    assert '<span class="preheader"' in html_content
    # Assuming the preheader is included even if empty, check that it's empty
    assert "></span>" in html_content


def test_subject_and_preheader_provided():
    """
    Test that when subject and preheader are provided in the template,
    they override the default values.
    """
    # Send an email with subject and preheader in the template
    send_templated_mail(
        template_name="test_subject_preheader_provided",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Subject and preheader should be as provided in the template
    assert email.subject == "Subject from Template"
    html_content = email.alternatives[0][0]
    assert '<span class="preheader"' in html_content
    assert ">Preheader from Template</span>" in html_content


def test_rendering_local_links():
    """Test that local links are rendered correctly by premailer if base_url is provided."""
    import random  # pylint: disable=C0415

    from django.urls import reverse

    some_id = random.randint(1, 100)
    send_templated_mail(
        template_name="test_render_local_links",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        base_url="http://exampleeee.com",
        context={
            "name": "Test User",
            "some_id": some_id,
            "url": reverse("index", args=[some_id]),
        },
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    html_content = email.alternatives[0][0]

    url = reverse("index", args=[some_id])

    # Check that the email was sent
    assert email.subject == "Hello!"
    assert "Hello Test User!" in email.body
    assert "Hello Test User!" in html_content

    # Check that the link was rendered correctly twice
    assert html_content.count(f'<a href="http://exampleeee.com/{some_id}/"') == 2
    assert html_content.count(">index</a>") == 2


def test_custom_default_subject_and_preheader():
    """
    Test that the custom default subject and preheader from settings
    are used when not provided in the template or context.
    """
    settings.TEMPLATED_EMAIL_DEFAULT_SUBJECT = "Default Subject from Settings"
    settings.TEMPLATED_EMAIL_DEFAULT_PREHEADER = "Default Preheader from Settings"
    # Send an email without subject or preheader in template or context
    send_templated_mail(
        template_name="test_no_subject_preheader",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={"name": "Test User"},
    )

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Subject should be the custom default from settings
    assert email.subject == "Default Subject from Settings"
    # Preheader should be the custom default from settings
    html_content = email.alternatives[0][0]
    assert '<span class="preheader"' in html_content
    assert ">Default Preheader from Settings</span>" in html_content


def test_custom_html2text_settings(backend) -> None:
    """Test that custom html2text settings are properly applied."""
    # Set custom html2text settings
    backend.html2text_settings = {"ignore_links": True, "ignore_images": True, "body_width": 0}

    html_content = """
        <div>
            <p>Test content with <a href="http://example.com">a link</a></p>
            <img src="image.jpg" alt="test image">
        </div>
    """

    plain_text = backend._generate_plain_text(html_content)

    # Links and images should be ignored based on our settings
    assert "http://example.com" not in plain_text
    assert "test image" not in plain_text


def test_default_subject_preheader_settings(backend) -> None:
    """Test that default subject and preheader settings are used when not provided."""
    from django.test import override_settings

    custom_subject = "Custom Default Subject"
    custom_preheader = "Custom Default Preheader"

    with override_settings(
        TEMPLATED_EMAIL_DEFAULT_SUBJECT=custom_subject, TEMPLATED_EMAIL_DEFAULT_PREHEADER=custom_preheader
    ):
        # Create a new backend instance to pick up the settings
        new_backend = MarkdownTemplateBackend()
        assert new_backend.default_subject == custom_subject
        assert new_backend.default_preheader == custom_preheader


def test_fail_silently_render_email(backend) -> None:
    """Test that _render_email handles errors gracefully with fail_silently=True."""
    # Set fail_silently on the backend
    backend.fail_silently = True

    # Test with non-existent template
    result = backend._render_email(
        template_name="non_existent_template",
        context={},
    )

    # Should return fallback content
    assert result["html"] == "Email template rendering failed."
    assert result["plain"] == "Email template rendering failed."
    assert result["subject"] == backend.default_subject
    assert result["preheader"] == backend.default_preheader


def test_fail_silently_none_initialization() -> None:
    """Test that backend handles fail_silently=None during initialization."""
    from django.test import override_settings

    # When fail_silently is explicitly None, it should fall back to settings
    backend_with_none = MarkdownTemplateBackend(fail_silently=None)

    # Should use the default from settings (False in test settings)
    assert backend_with_none.fail_silently is False

    # Test with a setting override
    with override_settings(TEMPLATED_EMAIL_FAIL_SILENTLY=True):
        backend_with_setting = MarkdownTemplateBackend(fail_silently=None)
        assert backend_with_setting.fail_silently is True


def test_template_without_content_block(backend) -> None:
    """Test rendering a template without explicit {% block content %}."""
    result = backend._render_email(
        template_name="test_no_content_block",
        context={},
    )

    # Should extract content using fallback regex method
    assert "Simple Markdown" in result["html"]
    assert "<strong>Bold text</strong>" in result["html"]
    assert "<em>italic text</em>" in result["html"]
    # CSS inlining adds styles, so just check for content
    assert "List item 1" in result["html"]
    assert "List item 2" in result["html"]

    # Subject and preheader should still be extracted
    assert result["subject"] == "Test Email Without Content Block"
    assert result["preheader"] == "Test preheader"

    # Plain text should also work
    assert "Simple Markdown" in result["plain"]
    assert "Bold text" in result["plain"]


def test_markdown_render_error_with_fail_silently() -> None:
    """Test that MarkdownRenderError is caught when fail_silently=True."""
    from unittest.mock import patch
    from templated_email_md.exceptions import MarkdownRenderError

    backend = MarkdownTemplateBackend(fail_silently=True)

    # Mock markdown.markdown to raise an exception
    with patch("templated_email_md.backend.markdown.markdown") as mock_markdown:
        mock_markdown.side_effect = ValueError("Invalid markdown extension")

        # Should return the raw content instead of raising
        result = backend._render_markdown("# Test content")
        assert result == "# Test content"


def test_markdown_render_error_without_fail_silently() -> None:
    """Test that MarkdownRenderError is raised when fail_silently=False."""
    from unittest.mock import patch
    from templated_email_md.exceptions import MarkdownRenderError

    backend = MarkdownTemplateBackend(fail_silently=False)

    # Mock markdown.markdown to raise an exception
    with patch("templated_email_md.backend.markdown.markdown") as mock_markdown:
        mock_markdown.side_effect = ValueError("Invalid markdown extension")

        # Should raise MarkdownRenderError
        with pytest.raises(MarkdownRenderError) as exc_info:
            backend._render_markdown("# Test content")

        assert "Invalid markdown extension" in str(exc_info.value)


def test_css_inlining_error_with_fail_silently() -> None:
    """Test that CSSInliningError is caught when fail_silently=True."""
    from unittest.mock import patch
    from templated_email_md.exceptions import CSSInliningError

    backend = MarkdownTemplateBackend(fail_silently=True)

    # Mock premailer.transform to raise an exception
    with patch("templated_email_md.backend.premailer.transform") as mock_premailer:
        mock_premailer.side_effect = OSError("Network error fetching CSS")

        # Should return the original HTML instead of raising
        test_html = "<p>Test content</p>"
        result = backend._inline_css(test_html, base_url="http://example.com")
        assert result == test_html


def test_css_inlining_error_without_fail_silently() -> None:
    """Test that CSSInliningError is raised when fail_silently=False."""
    from unittest.mock import patch
    from templated_email_md.exceptions import CSSInliningError

    backend = MarkdownTemplateBackend(fail_silently=False)

    # Mock premailer.transform to raise an exception
    with patch("templated_email_md.backend.premailer.transform") as mock_premailer:
        mock_premailer.side_effect = OSError("Network error fetching CSS")

        # Should raise CSSInliningError
        with pytest.raises(CSSInliningError) as exc_info:
            backend._inline_css("<p>Test content</p>", base_url="http://example.com")

        assert "Network error fetching CSS" in str(exc_info.value)


def test_plain_text_generation_error_with_fail_silently() -> None:
    """Test that plain text generation errors are caught when fail_silently=True."""
    from unittest.mock import patch

    backend = MarkdownTemplateBackend(fail_silently=True)

    # Mock html2text to raise an exception
    with patch("templated_email_md.backend.html2text.HTML2Text") as mock_html2text:
        mock_instance = mock_html2text.return_value
        mock_instance.handle.side_effect = AttributeError("Invalid HTML structure")

        # Should return fallback content instead of raising
        result = backend._get_plain_text_content_from_template("<p>Test</p>")
        assert result == "Email template rendering failed."


def test_plain_text_generation_error_without_fail_silently() -> None:
    """Test that plain text generation errors are raised when fail_silently=False."""
    from unittest.mock import patch

    backend = MarkdownTemplateBackend(fail_silently=False)

    # Mock html2text to raise an exception
    with patch("templated_email_md.backend.html2text.HTML2Text") as mock_html2text:
        mock_instance = mock_html2text.return_value
        mock_instance.handle.side_effect = AttributeError("Invalid HTML structure")

        # Should raise AttributeError
        with pytest.raises(AttributeError) as exc_info:
            backend._get_plain_text_content_from_template("<p>Test</p>")

        assert "Invalid HTML structure" in str(exc_info.value)


def test_context_base_url_restoration(backend) -> None:
    """Test that _base_url in context is properly restored after send()."""
    from django.core import mail

    # Create context with a pre-existing _base_url
    context = {
        "name": "Test User",
        "_base_url": "http://original-url.com",
    }

    # Send email with a different base_url
    backend.send(
        template_name="test_message",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
        context=context,
        base_url="http://new-url.com",
    )

    # Context should be restored to original value
    assert context["_base_url"] == "http://original-url.com"


def test_markdown_import_error() -> None:
    """Test handling of ImportError when markdown extension is not found."""
    from unittest.mock import patch
    from templated_email_md.exceptions import MarkdownRenderError

    backend = MarkdownTemplateBackend(fail_silently=False)

    # Mock markdown.markdown to raise ImportError
    with patch("templated_email_md.backend.markdown.markdown") as mock_markdown:
        mock_markdown.side_effect = ImportError("Extension 'invalid.extension' not found")

        # Should raise MarkdownRenderError
        with pytest.raises(MarkdownRenderError) as exc_info:
            backend._render_markdown("# Test content")

        assert "Extension 'invalid.extension' not found" in str(exc_info.value)


def test_build_preview_page_returns_full_html_document():
    """build_preview_page must return a string starting with <!DOCTYPE html>."""
    from templated_email_md.preview import build_preview_page

    result = build_preview_page(
        subject="Hello World",
        preheader="A short preview",
        html_body="<p>Body</p>",
        plain="Body",
    )
    assert result.startswith("<!DOCTYPE html>")


def test_build_preview_page_contains_subject_and_preheader():
    """build_preview_page must embed subject and preheader in the wrapper chrome."""
    from templated_email_md.preview import build_preview_page

    result = build_preview_page(
        subject="My Subject",
        preheader="My Preheader",
        html_body="<p>x</p>",
        plain="x",
    )
    assert "My Subject" in result
    assert "My Preheader" in result


def test_build_preview_page_html_escaped_in_srcdoc():
    """HTML email content must be html.escape()'d before insertion into srcdoc."""
    from templated_email_md.preview import build_preview_page

    raw_html = '<p style="color:red">Hello & "World"</p>'
    escaped = html_stdlib.escape(raw_html, quote=True)
    result = build_preview_page(
        subject="S",
        preheader="P",
        html_body=raw_html,
        plain="Hello",
    )
    assert escaped in result
    # The unescaped ampersand must NOT appear raw inside the srcdoc attribute
    assert ' & "' not in result


def test_build_preview_page_plain_text_appears():
    """Plain text version must appear verbatim inside a <pre> element."""
    from templated_email_md.preview import build_preview_page

    result = build_preview_page(
        subject="S",
        preheader="P",
        html_body="<p>x</p>",
        plain="Plain text line one\nLine two",
    )
    assert "Plain text line one" in result
    assert "Line two" in result


def test_file_changed_returns_false_when_mtime_unchanged(tmp_path):
    """file_changed must return (False, mtime) when file has not been modified."""
    from templated_email_md.preview import file_changed

    f = tmp_path / "tpl.md"
    f.write_text("{% block content %}hi{% endblock %}")
    mtime = f.stat().st_mtime
    changed, new_mtime = file_changed(str(f), mtime)
    assert changed is False
    assert new_mtime == mtime


def test_file_changed_returns_true_after_utime(tmp_path):
    """file_changed must return (True, new_mtime) after the file's mtime advances."""
    from templated_email_md.preview import file_changed

    f = tmp_path / "tpl.md"
    f.write_text("{% block content %}hi{% endblock %}")
    mtime = f.stat().st_mtime
    # Move mtime 10 seconds into the future
    future = mtime + 10
    os.utime(str(f), (future, future))
    changed, new_mtime = file_changed(str(f), mtime)
    assert changed is True
    assert new_mtime == future


def test_preview_email_management_command_is_discoverable():
    """Django must be able to load the preview_email management command."""
    from django.core.management import load_command_class

    cmd_class = load_command_class("templated_email_md", "preview_email")
    assert cmd_class is not None


def test_preview_email_writes_html_file(tmp_path):
    """preview_email must write a full HTML document containing rendered content."""
    output_file = tmp_path / "out.html"
    call_command(
        "preview_email",
        "test_message",
        "--context",
        '{"name": "Preview User"}',
        "--output",
        str(output_file),
    )
    assert output_file.exists(), "Output file was not created"
    content = output_file.read_text(encoding="utf-8")
    assert content.startswith("<!DOCTYPE html>"), "Output is not a full HTML document"
    assert "Preview User" in content, "Context variable not rendered into output"
    assert "Test Email" in content, "Subject not present in output"


def test_preview_email_part_subject_prints_to_stdout():
    """preview_email --part subject must print the subject to stdout."""
    stdout_buf = io.StringIO()
    call_command(
        "preview_email",
        "test_message",
        "--context",
        '{"name": "Preview User"}',
        "--part",
        "subject",
        stdout=stdout_buf,
    )
    output = stdout_buf.getvalue()
    assert "Test Email" in output, f"Expected 'Test Email' in stdout, got: {output!r}"


def test_preview_email_part_plain_prints_to_stdout():
    """preview_email --part plain must print the plain text body to stdout."""
    stdout_buf = io.StringIO()
    call_command(
        "preview_email",
        "test_message",
        "--context",
        '{"name": "Preview User"}',
        "--part",
        "plain",
        stdout=stdout_buf,
    )
    output = stdout_buf.getvalue()
    assert "Preview User" in output, f"Expected rendered name in plain output, got: {output!r}"


def test_preview_email_raises_command_error_for_missing_template():
    """preview_email must raise CommandError when the template does not exist."""
    with pytest.raises(CommandError):
        call_command(
            "preview_email",
            "nonexistent_template_xyz",
        )


def test_preview_email_context_file(tmp_path):
    """preview_email --context-file must load context from a JSON file."""
    context_file = tmp_path / "ctx.json"
    context_file.write_text('{"name": "FileUser"}', encoding="utf-8")
    output_file = tmp_path / "out_ctx_file.html"
    call_command(
        "preview_email",
        "test_message",
        "--context-file",
        str(context_file),
        "--output",
        str(output_file),
    )
    content = output_file.read_text(encoding="utf-8")
    assert "FileUser" in content


def test_preview_email_inline_context_wins_over_context_file(tmp_path):
    """Inline --context must take precedence over --context-file when both supplied."""
    context_file = tmp_path / "ctx.json"
    context_file.write_text('{"name": "FileUser"}', encoding="utf-8")
    output_file = tmp_path / "out_precedence.html"
    call_command(
        "preview_email",
        "test_message",
        "--context",
        '{"name": "InlineUser"}',
        "--context-file",
        str(context_file),
        "--output",
        str(output_file),
    )
    content = output_file.read_text(encoding="utf-8")
    assert "InlineUser" in content
    assert "FileUser" not in content


def test_watch_render_once_round_trip(tmp_path):
    """A single _render + _write_preview cycle must produce correct output.

    This exercises the watch-mode code path without entering the infinite loop,
    confirming that re-rendering after a file change produces a valid preview.
    """
    output_file = tmp_path / "watch_out.html"

    # Initial render
    call_command(
        "preview_email",
        "test_message",
        "--context",
        '{"name": "WatchUser"}',
        "--output",
        str(output_file),
    )
    first_content = output_file.read_text(encoding="utf-8")
    assert "WatchUser" in first_content

    # Simulate re-render by calling call_command again (as --watch would do internally)
    call_command(
        "preview_email",
        "test_message",
        "--context",
        '{"name": "WatchUserV2"}',
        "--output",
        str(output_file),
    )
    second_content = output_file.read_text(encoding="utf-8")
    assert "WatchUserV2" in second_content
    assert second_content.startswith("<!DOCTYPE html>")


def test_preview_email_invalid_json_raises_command_error():
    """preview_email --context with invalid JSON must raise CommandError."""
    with pytest.raises(CommandError):
        call_command("preview_email", "test_message", "--context", "{bad json")


def test_preview_email_missing_context_file_raises_command_error(tmp_path):
    """preview_email --context-file pointing at a nonexistent path must raise CommandError."""
    with pytest.raises(CommandError):
        call_command("preview_email", "test_message", "--context-file", str(tmp_path / "nope.json"))


def test_preview_email_nondict_context_raises_command_error():
    """preview_email --context with a non-object JSON value must raise CommandError."""
    with pytest.raises(CommandError):
        call_command("preview_email", "test_message", "--context", "[1, 2, 3]")


def test_branding_defaults() -> None:
    """Test that a fresh backend with no TEMPLATED_EMAIL_BRANDING setting has correct defaults."""
    from django.test import override_settings

    with override_settings(TEMPLATED_EMAIL_BRANDING={}):
        fresh_backend = MarkdownTemplateBackend()
        assert fresh_backend.branding["primary_color"] == "#3498db"
        assert fresh_backend.branding["link_color"] == "#3498db"
        assert fresh_backend.branding["heading_color"] == "#000000"
        assert fresh_backend.branding["text_color"] == "#333333"
        assert fresh_backend.branding["background_color"] == "#f6f6f6"
        assert fresh_backend.branding["container_background"] == "#ffffff"
        assert fresh_backend.branding["font_family"] == "sans-serif"
        assert fresh_backend.branding["logo_url"] == ""
        assert fresh_backend.branding["logo_alt"] == ""
        assert fresh_backend.branding["logo_width"] == "200"


def test_branding_merge_preserves_defaults() -> None:
    """Test that user-supplied TEMPLATED_EMAIL_BRANDING merges over defaults without clobbering others."""
    from django.test import override_settings

    with override_settings(TEMPLATED_EMAIL_BRANDING={"primary_color": "#ff0000"}):
        fresh_backend = MarkdownTemplateBackend()
        # User override applied
        assert fresh_backend.branding["primary_color"] == "#ff0000"
        # Untouched defaults preserved
        assert fresh_backend.branding["font_family"] == "sans-serif"
        assert fresh_backend.branding["background_color"] == "#f6f6f6"
        assert fresh_backend.branding["logo_url"] == ""


def test_branding_context_backward_compatible(backend) -> None:
    """Test that default branding reproduces the current look (backward compat regression)."""
    response = backend._render_email("test_message", {"name": "X"})
    # Default primary_color (#3498db) must appear somewhere in the rendered HTML
    # (either inlined by premailer or in a remaining <style> tag)
    assert "#3498db" in response["html"]


def test_branding_css_overrides_applied() -> None:
    """Test that TEMPLATED_EMAIL_BRANDING colors appear in rendered HTML output."""
    from django.test import override_settings

    with override_settings(
        TEMPLATED_EMAIL_BRANDING={
            "background_color": "#112233",
            "link_color": "#abcabc",
            "primary_color": "#deed00",
        }
    ):
        fresh_backend = MarkdownTemplateBackend()
        # background_color and link_color against test_message (has <body> and <a> link)
        response_msg = fresh_backend._render_email("test_message", {"name": "X"})
        assert "#112233" in response_msg["html"], "background_color not found in rendered HTML"
        assert "#abcabc" in response_msg["html"], "link_color not found in rendered HTML"
        # primary_color against test_button_component (has .btn-primary element to inline onto)
        response_btn = fresh_backend._render_email("test_button_component", {})
        assert "#deed00" in response_btn["html"], "primary_color not found in rendered HTML"


def test_branding_logo_rendered_when_provided() -> None:
    """Test that a logo <img> appears in output when logo_url is set."""
    from django.test import override_settings

    with override_settings(
        TEMPLATED_EMAIL_BRANDING={
            "logo_url": "https://cdn.example.com/logo.png",
            "logo_alt": "Acme",
            "logo_width": "150",
        }
    ):
        fresh_backend = MarkdownTemplateBackend()
        response = fresh_backend._render_email("test_message", {"name": "X"})
        assert 'src="https://cdn.example.com/logo.png"' in response["html"], "logo src not found"
        assert 'alt="Acme"' in response["html"], "logo alt not found"


def test_branding_logo_absent_when_not_provided() -> None:
    """Test that no logo <img> appears when logo_url is empty (the default)."""
    from django.test import override_settings

    with override_settings(TEMPLATED_EMAIL_BRANDING={}):
        fresh_backend = MarkdownTemplateBackend()
        response = fresh_backend._render_email("test_message", {"name": "X"})
        # The logo src placeholder must not appear - no stray <img> from the logo block
        assert "https://cdn.example.com/logo.png" not in response["html"]
        # More generally: when logo_url is empty the branding logo block emits nothing,
        # so we should not find an img tag whose src is empty (which would be malformed).
        # We cannot assert no <img> at all since markdown_styles might produce none anyway,
        # but we can assert the logo sentinel attribute is absent.
        assert 'class="branding-logo"' not in response["html"]


def test_dark_mode_meta_tags(backend) -> None:
    """Test that dark-mode color-scheme meta tags are present in rendered HTML."""
    response = backend._render_email("test_message", {"name": "Test User"})

    assert 'name="color-scheme"' in response["html"]
    assert 'content="light dark"' in response["html"]
    assert 'name="supported-color-schemes"' in response["html"]


def test_dark_mode_css(backend) -> None:
    """Test that dark-mode @media block is preserved in rendered HTML by premailer."""
    response = backend._render_email("test_message", {"name": "Test User"})

    # premailer preserves @media rules it cannot inline; the block must survive
    assert "prefers-color-scheme" in response["html"]
    # Assert the specific dark background colour chosen for body/.body
    assert "#1a1a1a" in response["html"]
    # Assert the dark background for .main
    assert "#2a2a2a" in response["html"]


def test_button_component(backend) -> None:
    """Test that the button component partial renders a bulletproof button in the email HTML."""
    response = backend._render_email("test_button_component", {})

    # The button anchor must have the correct href
    assert 'href="https://example.com/go"' in response["html"]
    # The button label text must appear
    assert "Click Me" in response["html"]
    # The button outer wrapper table must have the btn class
    assert 'class="btn btn-primary"' in response["html"]
    # The anchor must include rel for security
    assert 'rel="noopener noreferrer"' in response["html"]


def test_divider_component(backend) -> None:
    """Test that the divider component partial renders a horizontal rule in the email HTML."""
    response = backend._render_email("test_divider_component", {})

    # The divider table must be present
    assert 'class="email-divider"' in response["html"]
    # The divider cell must carry the inline border styling applied by premailer
    assert "border-bottom" in response["html"]
    # Content around the divider must also render
    assert "Above the divider" in response["html"]
    assert "Below the divider" in response["html"]
    # Dark-mode override rule must be preserved in the rendered style block
    # (premailer normalises #444444 to #444, so match the shortened form)
    assert "email-divider td" in response["html"]
    assert "border-bottom-color: #444" in response["html"]


def test_sanitize_setting_default_is_false(backend) -> None:
    """Test that TEMPLATED_EMAIL_SANITIZE defaults to False."""
    assert backend.sanitize is False


def test_sanitize_settings_read_from_django_settings() -> None:
    """Test that TEMPLATED_EMAIL_SANITIZE and TEMPLATED_EMAIL_SANITIZE_KWARGS are read from settings."""
    from django.test import override_settings

    custom_kwargs = {"tags": {"p", "a", "strong", "em"}}

    with override_settings(TEMPLATED_EMAIL_SANITIZE=True, TEMPLATED_EMAIL_SANITIZE_KWARGS=custom_kwargs):
        new_backend = MarkdownTemplateBackend()
        assert new_backend.sanitize is True
        assert new_backend.sanitize_kwargs == custom_kwargs


def test_sanitize_html_removes_script_tags() -> None:
    """Test that _sanitize_html removes script tags and retains safe content."""
    sanitizing_backend = MarkdownTemplateBackend()
    dirty = "<p>Hello world</p><script>alert('xss')</script>"
    result = sanitizing_backend._sanitize_html(dirty)
    assert "<script>" not in result
    assert "alert" not in result
    assert "Hello world" in result


def test_sanitize_html_fail_silently_returns_input_on_error() -> None:
    """Test that _sanitize_html returns input unchanged when fail_silently=True and nh3 raises."""
    from unittest.mock import patch

    sanitizing_backend = MarkdownTemplateBackend(fail_silently=True)
    dirty = "<p>test</p>"

    with patch("templated_email_md.backend.nh3") as mock_nh3:
        mock_nh3.clean.side_effect = RuntimeError("unexpected nh3 error")
        result = sanitizing_backend._sanitize_html(dirty)

    assert result == dirty


def test_sanitize_html_raises_on_error_without_fail_silently() -> None:
    """Test that _sanitize_html raises when fail_silently=False and nh3 raises."""
    from unittest.mock import patch

    sanitizing_backend = MarkdownTemplateBackend(fail_silently=False)

    with patch("templated_email_md.backend.nh3") as mock_nh3:
        mock_nh3.clean.side_effect = RuntimeError("unexpected nh3 error")
        with pytest.raises(RuntimeError, match="unexpected nh3 error"):
            sanitizing_backend._sanitize_html("<p>test</p>")


def test_xss_content_present_without_sanitization(backend) -> None:
    """Test that script tags survive rendering when TEMPLATED_EMAIL_SANITIZE is False (default).

    This documents the current behavior: markdown passes raw HTML through, so a
    script tag in the content block reaches the final HTML. Sanitization must be
    explicitly enabled to prevent this.
    """
    result = backend._render_email("test_xss_content", {})
    assert "<script>" in result["html"], "Expected <script> to be present in HTML when sanitization is off"


def test_xss_content_removed_with_sanitization() -> None:
    """Test that script tags are removed when TEMPLATED_EMAIL_SANITIZE=True."""
    from django.test import override_settings

    with override_settings(TEMPLATED_EMAIL_SANITIZE=True):
        sanitizing_backend = MarkdownTemplateBackend()
        result = sanitizing_backend._render_email("test_xss_content", {})

    assert "<script>" not in result["html"], "Expected <script> to be absent from HTML when sanitization is on"
    assert "Normal paragraph text" in result["html"], "Expected safe content to survive sanitization"
    assert "More safe content here" in result["html"], "Expected safe content to survive sanitization"
    assert result["subject"] == "XSS Test Email"


def test_sanitize_html_raises_importerror_when_nh3_missing() -> None:
    """_sanitize_html raises ImportError when nh3 is not installed, even with fail_silently=True."""
    from unittest.mock import patch

    # fail_silently=True must still raise ImportError (a missing optional dep is a
    # misconfiguration; silently skipping requested sanitization would be unsafe)
    backend = MarkdownTemplateBackend(fail_silently=True)
    with patch("templated_email_md.backend.nh3", None):
        with pytest.raises(ImportError, match="sanitize"):
            backend._sanitize_html("<p>hi</p>")
