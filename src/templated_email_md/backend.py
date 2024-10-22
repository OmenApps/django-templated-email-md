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
        self.template_suffix = template_suffix or getattr(settings, 'TEMPLATED_EMAIL_FILE_EXTENSION', 'md')
        self.fail_silently = fail_silently
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
        if extension.startswith('.'):
            extension = extension[1:]

        prefix = template_dir if template_dir else (self.template_prefix or '')
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
                subject = template_content[subject_start + 19:subject_end].strip()
                # Render any template variables in subject
                subject_template = Template(subject)
                blocks['subject'] = subject_template.render(Context(context))
                # Remove subject block from content
                template_content = (
                    template_content[:subject_start].strip() +
                    template_content[subject_end + 13:].strip()
                )

        blocks['content'] = template_content.strip()
        return blocks

    def _generate_plain_text(self, html_content: str) -> str:
        """Generate plain text content from HTML.

        Args:
            html_content: HTML content to convert

        Returns:
            Plain text content without Markdown formatting
        """
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        h.ignore_emphasis = True  # Do not add '*' around bold/italic text
        h.mark_code = False       # Do not add backticks around code
        h.wrap_links = False      # Do not wrap links in brackets
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
                template_name if isinstance(template_name, str) else template_name[0],
                template_dir,
                file_extension
            )

            # Use render_block_to_string to get 'subject' block
            try:
                subject = render_block_to_string(template_path, 'subject', context).strip()
            except BlockNotFound:
                subject = _("No Subject")

            # Override subject if 'subject' is in context
            subject = context.get('subject', subject)

            # Use render_block_to_string to get 'content' block
            try:
                content = render_block_to_string(template_path, 'content', context).strip()
            except BlockNotFound:
                # If 'content' block is not defined, render the entire template without the 'subject' block
                md_template = get_template(template_path)
                template_source = md_template.template.source
                # Remove the 'subject' block from the template source
                pattern = r'{% block subject %}.*?{% endblock %}'
                content_without_subject = re.sub(pattern, '', template_source, flags=re.DOTALL).strip()
                content_template = Template(content_without_subject)
                content = content_template.render(Context(context))

            # Convert markdown content to HTML
            html_content = self._render_markdown(content)

            # Get the base template
            base_template = get_template(self.base_html_template)

            # Create context for base template with all needed variables
            base_context = {
                **context,  # Original context
                'markdown_content': html_content,
                'subject': context.get('subject', subject),
            }

            # Render base template
            rendered_html = base_template.render(base_context)

            # Inline CSS
            inlined_html = self._inline_css(rendered_html)

            # Generate plain text from HTML content (not the full email template)
            plain_text = self._generate_plain_text(html_content)

            return {
                'html': inlined_html,
                'plain': plain_text,
                'subject': subject,
            }

        except Exception as e:
            logger.error("Failed to render email: %s", str(e))
            if self.fail_silently:
                return {
                    'html': fallback_content,
                    'plain': fallback_content,
                    'subject': _("No Subject"),
                }
            raise

    def _get_subject_from_template(self, context: Dict[str, Any]) -> Optional[str]:
        """Extract subject from template block."""
        try:
            return render_block_to_string(
                [self.base_html_template], "subject", context
            ).strip()
        except BlockNotFound:
            return None
