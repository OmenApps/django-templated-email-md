"""Test cases for the django-templated-email-md package."""

import pytest
from django.conf import settings
from django.core import mail
from django.template import TemplateDoesNotExist
from django.utils import translation
from django.utils.translation import gettext as _
from templated_email import send_templated_mail

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
    assert "Preheader from Template" not in email.body  # Should not be in plain text


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
    assert "Preheader from Context" not in email.body  # Should not be in plain text


def test_remove_comments():
    """Test that HTML and JavaScript comments are removed from the HTML content."""
    backend = MarkdownTemplateBackend()
    html_with_comments = """
    <!-- HTML Comment -->
    <div>
      Content here
      <!-- Another comment -->
      <style>
        /* CSS Comment */
        .class { color: red; }
      </style>
      <script>
        /* JavaScript Comment */
        var x = 1;
      </script>
    </div>
    """
    cleaned_html = backend._remove_comments(html_with_comments)  # pylint: disable=W0212

    assert "<!--" not in cleaned_html
    assert "-->" not in cleaned_html
    assert "/*" not in cleaned_html
    assert "*/" not in cleaned_html
    assert "HTML Comment" not in cleaned_html
    assert "CSS Comment" not in cleaned_html
    assert "JavaScript Comment" not in cleaned_html


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
