"""Backend that uses Django templates and allows writing email content in Markdown."""

import hashlib
import json
import logging
import re
from typing import Any

import html2text
import markdown
import premailer
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import caches
from django.template import Context
from django.template import Template
from django.template import TemplateDoesNotExist
from django.template import TemplateSyntaxError
from django.template.loader import get_template
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from render_block import BlockNotFound
from render_block import render_block_to_string
from templated_email.backends.vanilla_django import TemplateBackend

from templated_email_md.exceptions import CSSInliningError
from templated_email_md.exceptions import MarkdownRenderError


try:
    import nh3
except ImportError:  # pragma: no cover
    nh3 = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

DEFAULT_BRANDING: dict[str, str] = {
    "primary_color": "#3498db",  # buttons & accents
    "link_color": "#3498db",
    "heading_color": "#000000",
    "text_color": "#333333",
    "background_color": "#f6f6f6",
    "container_background": "#ffffff",
    "font_family": "sans-serif",
    "logo_url": "",  # empty = no logo rendered
    "logo_alt": "",
    "logo_width": "200",  # px, used as width attr
}


class MarkdownTemplateBackend(TemplateBackend):
    """Backend that uses Django templates and allows writing email content in Markdown.

    It renders the Markdown into HTML, wraps it with a base template, and inlines CSS styling.
    The plain text version is generated from the final HTML using html2text.

    Cache settings (read from Django settings):
        TEMPLATED_EMAIL_CACHE_RENDERED (bool): Enable render result caching. Default False.
        TEMPLATED_EMAIL_CACHE_TIMEOUT (int): Cache TTL in seconds. Default 300.
        TEMPLATED_EMAIL_CACHE_ALIAS (str): Django cache alias to use. Default "default".
    """

    _CACHE_KEY_PREFIX = "templated_email_md:render:"

    def __init__(
        self,
        fail_silently: bool = False,
        template_prefix: str | None = None,
        template_suffix: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the MarkdownTemplateBackend.

        Args:
            fail_silently: Whether to suppress exceptions and return a fallback response
            template_prefix: Prefix for template names
            template_suffix: Suffix for template names
            kwargs: Additional keyword arguments
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
        self.default_subject = getattr(settings, "TEMPLATED_EMAIL_DEFAULT_SUBJECT", _lazy("Hello!"))
        self.default_preheader = getattr(settings, "TEMPLATED_EMAIL_DEFAULT_PREHEADER", _lazy(""))
        self.base_url = getattr(settings, "TEMPLATED_EMAIL_BASE_URL", "")
        self.branding: dict[str, str] = {
            **DEFAULT_BRANDING,
            **getattr(settings, "TEMPLATED_EMAIL_BRANDING", {}),
        }
        self.sanitize: bool = getattr(settings, "TEMPLATED_EMAIL_SANITIZE", False)
        self.sanitize_kwargs: dict[str, Any] = getattr(settings, "TEMPLATED_EMAIL_SANITIZE_KWARGS", {})
        self.cache_rendered: bool = getattr(settings, "TEMPLATED_EMAIL_CACHE_RENDERED", False)
        self.cache_timeout: int = getattr(settings, "TEMPLATED_EMAIL_CACHE_TIMEOUT", 300)
        self.cache_alias: str = getattr(settings, "TEMPLATED_EMAIL_CACHE_ALIAS", "default")

    def send(
        self,
        template_name: str | list | tuple,
        from_email: str,
        recipient_list: list[str],
        context: dict[str, Any],
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        fail_silently: bool = False,
        headers: dict[str, str] | None = None,
        template_prefix: str | None = None,
        template_suffix: str | None = None,
        template_dir: str | None = None,
        file_extension: str | None = None,
        auth_user: str | None = None,
        auth_password: str | None = None,
        connection: Any = None,
        attachments: list | None = None,
        create_link: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Send an email using the Markdown template.

        Overrides the send method to add support for a base URL, used by premailer to resolve relative URLs.

        Args:
            template_name: The name of the Markdown template to render, or a list of names.
            from_email: The sender email address.
            recipient_list: List of recipient email addresses.
            context: The context dict used to render the template.
            cc: Optional list of CC email addresses.
            bcc: Optional list of BCC email addresses.
            fail_silently: Whether to suppress SMTP errors.
            headers: Optional extra email headers.
            template_prefix: Optional prefix for template names.
            template_suffix: Optional suffix (file extension) for template names.
            template_dir: Optional directory override for template lookup.
            file_extension: Optional file extension override.
            auth_user: Optional SMTP authentication username.
            auth_password: Optional SMTP authentication password.
            connection: Optional pre-opened email backend connection.
            attachments: Optional list of attachments to include.
            create_link: Whether to persist a link record via django-templated-email.
            kwargs: Additional keyword arguments forwarded to the parent send method.
                Pass ``base_url`` here to override the instance-level base URL for
                this call only.

        Returns:
            The return value of the parent send method (typically the number of
            messages sent, or None under the test email backend).
        """
        # Extract base_url from kwargs if provided, fall back to default
        base_url = kwargs.pop("base_url", self.base_url)

        # Add base_url to context temporarily for use in _render_email
        # Store original value if it exists to restore later
        context_had_base_url = "_base_url" in context
        original_base_url = context.get("_base_url")
        context["_base_url"] = base_url

        try:
            return super().send(
                template_name,
                from_email,
                recipient_list,
                context,
                cc=cc,
                bcc=bcc,
                fail_silently=fail_silently,
                headers=headers,
                template_prefix=template_prefix,
                template_suffix=template_suffix,
                template_dir=template_dir,
                file_extension=file_extension,
                auth_user=auth_user,
                auth_password=auth_password,
                connection=connection,
                attachments=attachments,
                create_link=create_link,
                **kwargs,
            )
        finally:
            # Clean up context
            if context_had_base_url:
                context["_base_url"] = original_base_url
            else:
                context.pop("_base_url", None)

    async def asend(self, *args: Any, **kwargs: Any) -> Any:
        """Send an email asynchronously by wrapping the synchronous :meth:`send`.

        Offloads the blocking render pipeline (Markdown conversion, CSS inlining
        via Premailer, html2text) and SMTP delivery to a thread pool via
        :func:`asgiref.sync.sync_to_async`, making it safe to ``await`` from
        async Django views, ASGI middleware, or async task queues.

        ``thread_sensitive=True`` is used because :meth:`send` may perform ORM
        writes (e.g. when ``create_link=True``, django-templated-email persists
        a record), and thread-sensitive execution keeps that compatible with
        Django's per-thread database connections.

        All positional and keyword arguments are forwarded unchanged to
        :meth:`send`. See :meth:`send` for the full parameter reference.

        Args:
            args: Positional arguments forwarded to :meth:`send`.
            kwargs: Keyword arguments forwarded to :meth:`send`.

        Returns:
            Any: The return value of :meth:`send` (typically ``None`` under the
            test email backend, matching Django's locmem backend convention).
        """
        return await sync_to_async(self.send, thread_sensitive=True)(*args, **kwargs)

    def _render_cache_key(
        self,
        template_name: str | list | tuple,
        context: dict[str, Any],
        template_dir: str | None,
        file_extension: str | None,
    ) -> str | None:
        """Build a deterministic SHA-256 cache key for a rendered email.

        The key encodes: template name, template_dir, file_extension, base HTML
        template name, active language, resolved base_url, and a JSON dump of
        context (with the private ``_base_url`` key excluded). It also encodes
        all rendering-relevant settings (markdown extensions, html2text settings,
        sanitize flags, branding, template suffix, and template prefix) so that
        a settings change produces a different key and does not serve stale
        cached HTML.

        Only JSON-serializable contexts and settings are cached. If ``json.dumps``
        raises ``TypeError`` or ``ValueError`` (e.g. the context contains a plain
        ``object()``, or ``sanitize_kwargs`` contains a ``set``), this method
        returns ``None`` to signal that the result should not be cached for that
        call (safe fallback - caching is simply skipped).

        Args:
            template_name: The Markdown template name or list of names.
            context: The render context dict. The ``_base_url`` key is handled
                separately and excluded from the context portion of the hash.
            template_dir: Optional template directory override.
            file_extension: Optional file extension override.

        Returns:
            A ``"templated_email_md:render:<hex-digest>"`` string when the
            context is serializable, or ``None`` when it is not.
        """
        # Normalise template_name to a stable JSON-serializable form
        if isinstance(template_name, (list, tuple)):
            normalised_name = list(template_name)
        else:
            normalised_name = template_name

        # _base_url is injected by send() and must be part of the key (different
        # base URLs produce different inlined CSS), but it must NOT appear in the
        # context portion (to keep context-hash stable across send() calls).
        base_url_for_key = context.get("_base_url", self.base_url)

        # Build context copy without the private key
        context_for_hash = {k: v for k, v in context.items() if k != "_base_url"}

        payload = {
            "template_name": normalised_name,
            "template_dir": template_dir,
            "file_extension": file_extension,
            "base_html_template": self.base_html_template,
            "language": get_language(),
            "base_url": base_url_for_key,
            "context": context_for_hash,
            "markdown_extensions": self.markdown_extensions,
            "html2text_settings": self.html2text_settings,
            "sanitize": self.sanitize,
            "sanitize_kwargs": self.sanitize_kwargs,
            "branding": self.branding,
            "template_suffix": file_extension or self.template_suffix,
            "template_prefix": template_dir or (self.template_prefix or ""),
        }

        try:
            serialised = json.dumps(payload, sort_keys=True)
        except (TypeError, ValueError):
            return None

        digest = hashlib.sha256(serialised.encode()).hexdigest()
        return f"{self._CACHE_KEY_PREFIX}{digest}"

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
        except (ValueError, AttributeError, ImportError, TypeError) as e:
            logger.error("Failed to render Markdown: %s", e, exc_info=True)
            if self.fail_silently:
                return content  # Return raw content if conversion fails
            raise MarkdownRenderError(f"Failed to render Markdown: {e}") from e

    def _sanitize_html(self, html: str) -> str:
        """Sanitize HTML content to remove potentially dangerous tags and attributes.

        Uses the ``nh3`` library (Python bindings for the Rust ``ammonia`` crate).
        Only called when ``self.sanitize`` is ``True``. ``nh3`` must be installed via
        the ``sanitize`` optional extra::

            pip install django-templated-email-md[sanitize]

        Args:
            html: HTML string to sanitize.

        Returns:
            Sanitized HTML string with dangerous constructs removed.

        Raises:
            ImportError: If ``nh3`` is not installed and sanitization is requested.
            Exception: Re-raises any unexpected exception from ``nh3.clean`` when
                ``fail_silently`` is ``False``.
        """
        if nh3 is None:
            raise ImportError(
                "HTML sanitization requires the 'nh3' package. "
                "Install it with: pip install django-templated-email-md[sanitize]"
            )
        try:
            return nh3.clean(html, **self.sanitize_kwargs)
        except Exception as e:
            logger.error("Failed to sanitize HTML: %s", e, exc_info=True)
            if self.fail_silently:
                return html
            raise

    def _inline_css(self, html: str, base_url: str = "") -> str:
        """Inline CSS styles in HTML content.

        Args:
            html: HTML content to process
            base_url: Base URL for resolving relative URLs in CSS/images

        Returns:
            HTML with inlined CSS

        Raises:
            CSSInliningError: If CSS inlining fails
        """
        try:
            return premailer.transform(
                html=html,
                strip_important=False,
                keep_style_tags=False,
                cssutils_logging_level=logging.ERROR,
                base_url=base_url,
            )
        except (OSError, ValueError, AttributeError, TypeError) as e:
            logger.error("Failed to inline CSS: %s", e, exc_info=True)
            if self.fail_silently:
                return html  # Return original HTML if inlining fails
            raise CSSInliningError(f"Failed to inline CSS: {e}") from e

    def _get_template_path(self, template_name: str, template_dir: str | None, file_extension: str | None) -> str:
        """Construct the full template path.

        Args:
            template_name: The name of the template
            template_dir: The directory to look for the template in
            file_extension: The file extension of the template file

        Returns:
            The full path to the template
        """
        extension = file_extension or self.template_suffix
        if extension.startswith("."):
            extension = extension[1:]

        prefix = template_dir if template_dir else (self.template_prefix or "")
        template_path = f"{prefix}{template_name}"
        if not template_path.endswith(f".{extension}"):
            template_path = f"{template_path}.{extension}"

        return template_path

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

    def _render_email_uncached(
        self,
        template_name: str | list | tuple,
        context: dict[str, Any],
        template_dir: str | None = None,
        file_extension: str | None = None,
    ) -> dict[str, str]:
        """Render the email content using the Markdown template and base HTML template.

        This is the raw, non-cached render path. Callers should prefer
        :meth:`_render_email`, which applies caching when
        ``TEMPLATED_EMAIL_CACHE_RENDERED`` is enabled.

        Args:
            template_name: The name of the Markdown template to render, or a list
                of names (first found is used).
            context: The context dict to render the template with.
            template_dir: Optional directory to look for the template in.
            file_extension: Optional file extension override.

        Returns:
            Dictionary with keys ``html``, ``plain``, ``subject``, and
            ``preheader``.

        Raises:
            TemplateDoesNotExist: If the template cannot be found and
                ``fail_silently`` is False.
            TemplateSyntaxError: If the template contains invalid syntax and
                ``fail_silently`` is False.
            MarkdownRenderError: If Markdown conversion fails and
                ``fail_silently`` is False.
            CSSInliningError: If CSS inlining fails and ``fail_silently`` is
                False.
            ValueError: If an invalid value is encountered during rendering and
                ``fail_silently`` is False.
            AttributeError: If an attribute error occurs during rendering and
                ``fail_silently`` is False.
            TypeError: If a type error occurs during rendering and
                ``fail_silently`` is False.
            OSError: If a filesystem error occurs while loading resources and
                ``fail_silently`` is False.
        """
        fallback_content = _("Email template rendering failed.")

        # Extract base_url from context (set by send() method)
        base_url = context.get("_base_url", self.base_url)

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
                "branding": self.branding,
            }

            # Render base template
            rendered_html = base_template.render(base_context)

            # Inline CSS with base_url for resolving relative URLs
            inlined_html = self._inline_css(rendered_html, base_url=base_url)

            # Remove comments from the final HTML message
            final_html = self._remove_comments(inlined_html)

            plain_text = self._get_plain_text_content_from_template(final_html)

            return {"html": final_html, "plain": plain_text, "subject": subject, "preheader": preheader}

        # BlockNotFound is caught internally by the _get_*_from_template helpers, so it cannot reach this handler.
        except (
            TemplateDoesNotExist,
            TemplateSyntaxError,
            MarkdownRenderError,
            CSSInliningError,
            ValueError,
            AttributeError,
            TypeError,
            OSError,
        ) as e:
            logger.error("Failed to render email: %s", str(e), exc_info=True)
            if self.fail_silently:
                return {
                    "html": fallback_content,
                    "plain": fallback_content,
                    "subject": self.default_subject,
                    "preheader": self.default_preheader,
                    "_render_failed": True,
                }
            raise

    def _render_email(
        self,
        template_name: str | list | tuple,
        context: dict[str, Any],
        template_dir: str | None = None,
        file_extension: str | None = None,
    ) -> dict[str, str]:
        """Render the email content, using the render cache when enabled.

        When ``TEMPLATED_EMAIL_CACHE_RENDERED`` is ``False`` (the default),
        this method is a transparent pass-through to
        :meth:`_render_email_uncached`. When caching is enabled, a
        deterministic SHA-256 key is computed from the template name, context,
        and other render parameters. If the key is already present in the
        configured cache, the cached dict is returned immediately, skipping the
        expensive Markdown-to-HTML + CSS-inlining pipeline. If the context is
        not JSON-serializable, the result is never cached (safe fallback).

        Args:
            template_name: The name of the Markdown template to render, or a list
                of names (first found is used).
            context: The context dict to render the template with.
            template_dir: Optional directory to look for the template in.
            file_extension: Optional file extension override.

        Returns:
            Dictionary with keys ``html``, ``plain``, ``subject``, and
            ``preheader``.
        """
        if not self.cache_rendered:
            result = self._render_email_uncached(template_name, context, template_dir, file_extension)
            result.pop("_render_failed", None)
            return result

        key = self._render_cache_key(template_name, context, template_dir, file_extension)
        if key is None:
            result = self._render_email_uncached(template_name, context, template_dir, file_extension)
            result.pop("_render_failed", None)
            return result

        cache = caches[self.cache_alias]
        cached = cache.get(key)
        logger.debug("render cache %s for %r", "hit" if cached is not None else "miss", template_name)
        if cached is not None:
            return cached

        result = self._render_email_uncached(template_name, context, template_dir, file_extension)
        failed = result.pop("_render_failed", False)
        if not failed:
            cache.set(key, result, self.cache_timeout)
        return result

    def _get_subject_from_template(self, template_path: str, context: dict[str, Any]) -> str | None:
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

    def _get_preheader_from_template(self, template_path: str, context: dict[str, Any]) -> str | None:
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
        context: dict[str, Any],
    ) -> str:
        """Extract content from template block.

        Args:
            template_path: Path to the template file
            context: Context to render the template with

        Returns:
            Rendered Markdown content string.
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
            content: Markdown content to convert

        Returns:
            Rendered HTML content.

        Raises:
            MarkdownRenderError: If Markdown conversion fails and fail_silently is False.
        """
        try:
            html_content = self._render_markdown(content)
        except MarkdownRenderError:
            if self.fail_silently:
                html_content = "Email template rendering failed."
            else:
                raise
        # Remove comments from the final HTML message
        html_content = self._remove_comments(html_content)
        # Optionally sanitize HTML to strip dangerous tags/attributes
        if self.sanitize:
            html_content = self._sanitize_html(html_content)
        return html_content

    def _get_plain_text_content_from_template(
        self,
        content: str,
    ) -> str:
        """Generate plain text content from HTML.

        Args:
            content: HTML content to convert

        Returns:
            Plain text content without Markdown formatting

        Raises:
            AttributeError: If an attribute error occurs during plain text generation.
            ValueError: If an invalid value is encountered during plain text generation.
            TypeError: If a type error occurs during plain text generation.
        """
        try:
            plain_text = self._generate_plain_text(content)
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error generating plain text: %s", e, exc_info=True)
            if self.fail_silently:
                plain_text = "Email template rendering failed."
            else:
                raise
        return plain_text

    def _remove_multiline_comments(self, html: str) -> str:
        """Remove multi-line JavaScript and CSS comments."""
        return re.sub(r"/\*[\s\S]*?\*/", "", html)

    def _remove_singleline_comments(self, html: str) -> str:
        """Remove single-line JavaScript and CSS comments while preserving URLs."""
        # Pattern to match // comments not preceded by :, ", ', or =
        pattern = r'(?<!:)(?<!")(?<!\')(?<!=)//.*?$'
        return re.sub(pattern, "", html, flags=re.MULTILINE)

    def _remove_html_comments(self, html: str) -> str:
        """Remove HTML comments but preserve IE conditional comments."""
        return re.sub(r"<!--(?!\[if).*?-->", "", html, flags=re.DOTALL)

    def _clean_extra_blank_lines(self, html: str) -> str:
        """Remove extra blank lines created by comment removal."""
        return re.sub(r"\n\s*\n", "\n", html)

    def _remove_comments(self, html: str) -> str:
        """Remove HTML, JavaScript, and CSS comments from HTML content while retaining URLs and IE-specific comments.

        Args:
            html: The HTML content containing comments.

        Returns:
            HTML content with comments removed.
        """
        html = self._remove_multiline_comments(html)
        html = self._remove_singleline_comments(html)
        html = self._remove_html_comments(html)
        html = self._clean_extra_blank_lines(html)
        return html
