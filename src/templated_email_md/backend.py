"""Backend that uses Django templates and allows writing email content in Markdown."""

import logging
import re
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import html2text
import markdown
import premailer
from django.conf import settings
from django.template import Context
from django.template import Template
from django.template.loader import get_template
from django.utils.translation import gettext as _
from render_block import BlockNotFound
from render_block import render_block_to_string
from templated_email.backends.vanilla_django import TemplateBackend

from templated_email_md.exceptions import CSSInliningError
from templated_email_md.exceptions import MarkdownRenderError


logger = logging.getLogger(__name__)


class MarkdownTemplateBackend(TemplateBackend):
    """Backend that uses Django templates and allows writing email content in Markdown.

    It renders the Markdown into HTML, wraps it with a base template, and inlines CSS styling.
    The plain text version is generated from the final HTML using html2text.
    """

    def __init__(
        self,
        fail_silently: bool = False,
        template_prefix: Optional[str] = None,
        template_suffix: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the MarkdownTemplateBackend.

        Args:
            fail_silently: Whether to suppress exceptions and return a fallback response
            template_prefix: Prefix for template names
            template_suffix: Suffix for template names
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            fail_silently=fail_silently,
            template_prefix=template_prefix,
            template_suffix=template_suffix,
            **kwargs,
        )
        if fail_silently is None:
            fail_silently = getattr(settings, "TEMPLATED_EMAIL_FAIL_SILENTLY", False)
        self.fail_silently = fail_silently
        self.template_suffix = template_suffix or getattr(settings, "TEMPLATED_EMAIL_FILE_EXTENSION", "md")
        self.base_html_template = getattr(
            settings,
            "TEMPLATED_EMAIL_BASE_HTML_TEMPLATE",
            "templated_email/markdown_base.html",
        )
        self.markdown_extensions = getattr(
            settings,
            "TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS",
            [
                "markdown.extensions.meta",
                "markdown.extensions.tables",
                "markdown.extensions.extra",
            ],
        )
        self.html2text_settings = getattr(settings, "TEMPLATED_EMAIL_HTML2TEXT_SETTINGS", {})
        self.default_subject = getattr(settings, "TEMPLATED_EMAIL_DEFAULT_SUBJECT", _("Hello!"))
        self.default_preheader = getattr(settings, "TEMPLATED_EMAIL_DEFAULT_PREHEADER", _(""))

    def _render_markdown(self, content: str) -> str:
        """Convert Markdown content to HTML.

        Args:
            content: Markdown content to convert

        Returns:
            Converted HTML content

        Raises:
            MarkdownRenderError: If Markdown conversion fails
        """
        try:
            return markdown.markdown(content, extensions=self.markdown_extensions)
        except Exception as e:
            logger.error("Failed to render Markdown: %s", e)
            if self.fail_silently:
                return content  # Return raw content if conversion fails
            raise MarkdownRenderError(f"Failed to render Markdown: {e}") from e

    def _inline_css(self, html: str) -> str:
        """Inline CSS styles in HTML content.

        Args:
            html: HTML content to process

        Returns:
            HTML with inlined CSS

        Raises:
            CSSInliningError: If CSS inlining fails
        """
        try:
            return premailer.transform(
                html=html,
                strip_important=False,
                keep_style_tags=True,
                cssutils_logging_level=logging.ERROR,
            )
        except Exception as e:
            logger.error("Failed to inline CSS: %s", e)
            if self.fail_silently:
                return html  # Return original HTML if inlining fails
            raise CSSInliningError(f"Failed to inline CSS: {e}") from e

    def _get_template_path(self, template_name: str, template_dir: Optional[str], file_extension: Optional[str]) -> str:
        """Construct the full template path."""
        extension = file_extension or self.template_suffix
        if extension.startswith("."):
            extension = extension[1:]

        prefix = template_dir if template_dir else (self.template_prefix or "")
        template_path = f"{prefix}{template_name}"
        if not template_path.endswith(f".{extension}"):
            template_path = f"{template_path}.{extension}"

        return template_path

    def _extract_blocks(self, template_content: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Extract and render template blocks."""
        blocks = {}

        # Find subject block
        subject_start = template_content.find("{% block subject %}")
        if subject_start != -1:
            subject_end = template_content.find("{% endblock %}", subject_start)
            if subject_end != -1:
                subject = template_content[subject_start + 19 : subject_end].strip()
                # Render any template variables in subject
                subject_template = Template(subject)
                blocks["subject"] = subject_template.render(Context(context))
                # Remove subject block from content
                template_content = (
                    template_content[:subject_start].strip() + template_content[subject_end + 13 :].strip()
                )

        blocks["content"] = template_content.strip()
        return blocks

    def _generate_plain_text(self, html_content: str) -> str:
        """Generate plain text content from HTML.

        Args:
            html_content: HTML content to convert

        Returns:
            Plain text content without Markdown formatting
        """
        h = html2text.HTML2Text()

        # Apply default settings
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        h.ignore_emphasis = True
        h.mark_code = False
        h.wrap_links = False

        # Override with user-defined settings
        for setting_name, setting_value in self.html2text_settings.items():
            setattr(h, setting_name, setting_value)

        return h.handle(html_content).strip()

    def _render_email(
        self,
        template_name: Union[str, list, tuple],
        context: Dict[str, Any],
        template_dir: Optional[str] = None,
        file_extension: Optional[str] = None,
    ) -> Dict[str, str]:
        """Render the email content using the Markdown template and base HTML template.

        Args:
            template_name (str or list): The name of the Markdown template to render.
            context (dict): The context to render the template with.
            template_dir (str): The directory to look for the template in.
            file_extension (str): The file extension of the template file.

        Returns:
            Dictionary containing the rendered HTML, plain text, and subject.
        """
        fallback_content = _("Email template rendering failed.")

        try:
            template_path = self._get_template_path(
                template_name if isinstance(template_name, str) else template_name[0], template_dir, file_extension
            )

            subject = self._get_subject_from_template(template_path, context)

            preheader = self._get_preheader_from_template(template_path, context)

            content = self._get_content_from_template(template_path, context)

            html_content = self._get_html_content_from_template(content)

            # Get the base template
            base_template = get_template(self.base_html_template)

            # Create context for base template with all needed variables
            base_context = {
                **context,  # Original context
                "markdown_content": html_content,
                "subject": context.get("subject", subject),
                "preheader": context.get("preheader", preheader),
            }

            # Render base template
            rendered_html = base_template.render(base_context)

            # Inline CSS
            inlined_html = self._inline_css(rendered_html)

            # Remove comments from the final HTML message
            rendered_html = self._remove_comments(rendered_html)

            plain_text = self._get_plain_text_content_from_template(html_content)

            return {"html": inlined_html, "plain": plain_text, "subject": subject, "preheader": preheader}

        except Exception as e:
            logger.error("Failed to render email: %s", str(e))
            if self.fail_silently:
                return {
                    "html": fallback_content,
                    "plain": fallback_content,
                    "subject": self.default_subject,
                    "preheader": self.default_preheader,
                }
            raise

    def _get_subject_from_template(self, template_path: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract subject from template block.

        Args:
            template_path: Path to the template file
            context: Context to render the template with

        Returns:
            Subject text
        """
        try:
            subject = render_block_to_string(template_path, "subject", context).strip()
        except BlockNotFound:
            subject = self.default_subject

        # Override subject if 'subject' is in context
        subject = context.get("subject", subject)

        return subject

    def _get_preheader_from_template(self, template_path: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract preheader from template block.

        Args:
            template_path: Path to the template file
            context: Context to render the template with

        Returns:
            Preheader text
        """
        try:
            preheader = render_block_to_string(template_path, "preheader", context).strip()
        except BlockNotFound:
            preheader = self.default_preheader

        # Override preheader if 'preheader' is in context
        preheader = context.get("preheader", preheader)

        return preheader

    def _get_content_from_template(
        self,
        template_path: str,
        context: Dict[str, Any],
    ) -> Dict[str, str]:
        """Extract content from template block.

        Args:
            template_path: Path to the template file
            context: Context to render the template with

        Returns:
            Dictionary containing the rendered HTML, plain text, and subject.
        """
        try:
            content = render_block_to_string(template_path, "content", context).strip()
        except BlockNotFound:
            # If 'content' block is not defined, render the entire template without 'subject' and 'preheader' blocks
            md_template = get_template(template_path)
            template_source = md_template.template.source
            # Remove the 'subject' and 'preheader' blocks from the template source
            patterns = [
                r"{% block subject %}.*?{% endblock %}",
                r"{% block subject %}.*?{% endblock subject %}",
                r"{% block preheader %}.*?{% endblock %}",
                r"{% block preheader %}.*?{% endblock preheader %}",
            ]
            content_without_subject_or_preheader = template_source
            for pattern in patterns:
                content_without_subject_or_preheader = re.sub(
                    pattern, "", content_without_subject_or_preheader, flags=re.DOTALL
                ).strip()

            content_template = Template(content_without_subject_or_preheader)
            content = content_template.render(Context(context))
        return content

    def _get_html_content_from_template(
        self,
        content: str,
    ) -> str:
        """Render the email content using the Markdown template and base HTML template.

        Args:
            template_name (str or list): The name of the Markdown template to render.
            context (dict): The context to render the template with.
            template_dir (str): The directory to look for the template in.
            file_extension (str): The file extension of the template file.

        Returns:
            Rendered HTML content.
        """
        try:
            html_content = self._render_markdown(content)
        except Exception as e:
            if self.fail_silently:
                logger.error("Error rendering email: %s", e)
                html_content = "Email template rendering failed."
            else:
                raise
        # Remove comments from the final HTML message
        html_content = self._remove_comments(html_content)
        return html_content

    def _get_plain_text_content_from_template(
        self,
        content: str,
    ) -> str:
        """Generate plain text content from HTML.

        Args:
            html_content: HTML content to convert

        Returns:
            Plain text content without Markdown formatting
        """
        try:
            plain_text = self._generate_plain_text(content)
        except Exception as e:
            if self.fail_silently:
                logger.error("Error generating plain text: %s", e)
                plain_text = "Email template rendering failed."
            else:
                raise
        return plain_text

    def _remove_comments(self, html: str) -> str:
        """Remove HTML comments and JavaScript/CSS comments from the HTML content."""
        # Remove HTML comments (excluding conditional comments for Outlook)
        html = re.sub(r"<!--(?!\[if).*?-->", "", html, flags=re.DOTALL)
        # Remove JavaScript and CSS comments
        html = re.sub(r"/\*.*?\*/", "", html, flags=re.DOTALL)
        return html
