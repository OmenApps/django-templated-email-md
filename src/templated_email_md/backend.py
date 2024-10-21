"""Backend that uses Django templates and allows writing email content in Markdown."""

import logging

import html2text
import markdown
import premailer
from django.conf import settings
from django.template import Context
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.translation import gettext as _
from render_block import BlockNotFound
from render_block import render_block_to_string
from templated_email.backends.vanilla_django import TemplateBackend


logger = logging.getLogger(__name__)


class MarkdownTemplateBackend(TemplateBackend):
    """Backend that uses Django templates and allows writing email content in Markdown.

    It renders the Markdown into HTML, wraps it with a base template, and inlines CSS styling.
    The plain text version is generated from the final HTML using html2text.
    """

    def __init__(self, fail_silently=False, template_prefix=None, template_suffix=None, **kwargs):
        super().__init__(
            fail_silently=fail_silently, template_prefix=template_prefix, template_suffix=template_suffix, **kwargs
        )
        self.base_html_template = getattr(
            settings, "TEMPLATED_EMAIL_BASE_HTML_TEMPLATE", "templated_email/markdown_base.html"
        )

    def _render_email(self, template_name, context, template_dir=None, file_extension=None):
        """Render the email content using the Markdown template and base HTML template.

        Args:
            template_name (str or list): The name of the Markdown template to render.
            context (dict): The context to render the template with.
            template_dir (str): The directory to look for the template in.
            file_extension (str): The file extension of the template file.

        Returns:
            dict: A dictionary containing the rendered HTML, plain text, and subject.
        """
        response = {}

        file_extension = file_extension or self.template_suffix
        if file_extension.startswith("."):
            file_extension = file_extension[1:]
        template_extension = f".{file_extension}"

        if isinstance(template_name, (tuple, list)):
            prefixed_templates = template_name
        else:
            prefixed_templates = [template_name]

        full_template_names = []
        for one_prefixed_template in prefixed_templates:
            one_full_template_name = "".join((template_dir or self.template_prefix, one_prefixed_template))
            if not one_full_template_name.endswith(template_extension):
                one_full_template_name += template_extension
            full_template_names.append(one_full_template_name)

        # Load the Markdown template
        for template_path in full_template_names:
            try:
                md_template = get_template(template_path)
                break
            except TemplateDoesNotExist:
                continue
        else:
            raise TemplateDoesNotExist(f"No Markdown email template found for {template_name}")

        # Render the Markdown template with context to get the Markdown content
        render_context = Context(context)
        md_content = md_template.render(render_context)

        # Convert the Markdown content to HTML
        html_message = markdown.markdown(
            md_content,
            extensions=[
                "markdown.extensions.meta",
                "markdown.extensions.tables",
                "markdown.extensions.extra",
            ],
        )

        # Load the base HTML template
        base_template = get_template(self.base_html_template)

        # Update context with rendered HTML content
        context["markdown_content"] = html_message

        # Render the base HTML template with context
        rendered_html = base_template.render(context)

        # Use Premailer to inline CSS
        inlined_html = premailer.transform(
            html=rendered_html,
            strip_important=False,
            keep_style_tags=True,
            cssutils_logging_level=logging.ERROR,
        )

        response["html"] = inlined_html

        # Generate plain text version using html2text
        response["plain"] = html2text.html2text(inlined_html)

        # Get the email subject
        if "subject" in context:
            response["subject"] = context["subject"]
        else:
            # Try to get 'subject' block from the base template
            try:
                subject = render_block_to_string([self.base_html_template], "subject", context)
                response["subject"] = subject.strip()
            except BlockNotFound:
                # Use default subject
                response["subject"] = _("No Subject")

        return response
