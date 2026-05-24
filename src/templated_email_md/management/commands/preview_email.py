"""Management command for rendering an email template to an HTML preview file."""

import json
import os
import webbrowser
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.template import TemplateDoesNotExist

from templated_email_md.backend import MarkdownTemplateBackend
from templated_email_md.preview import build_preview_page
from templated_email_md.preview import file_changed


_PART_CHOICES = ["all", "html", "plain", "subject", "preheader"]
_DEFAULT_OUTPUT = "email_preview.html"
_WATCH_INTERVAL_SECONDS = 1.0


class Command(BaseCommand):
    """Render a Markdown email template to a self-contained HTML preview file.

    The command instantiates ``MarkdownTemplateBackend``, renders the supplied
    template with an optional JSON context, wraps the output in a tri-pane preview
    page via ``build_preview_page``, and writes it to disk.  Passing ``--open``
    additionally opens the result in the system default browser.  Passing ``--part``
    prints a single section (``html``, ``plain``, ``subject``, or ``preheader``) to
    stdout instead of writing the full preview page.  Passing ``--watch`` enters an
    auto-reload loop that re-renders whenever the template file's mtime changes.
    """

    help = "Render a Markdown email template to an HTML preview file."

    def add_arguments(self, parser):
        """Register CLI arguments for the command.

        Args:
            parser: The argparse ``ArgumentParser`` instance provided by Django.
        """
        parser.add_argument(
            "template_name",
            type=str,
            help="Name of the Markdown email template to render (without extension).",
        )
        parser.add_argument(
            "--context",
            dest="context_inline",
            type=str,
            default=None,
            help="Template context as an inline JSON string (takes precedence over --context-file).",
        )
        parser.add_argument(
            "--context-file",
            dest="context_file",
            type=str,
            default=None,
            help="Path to a JSON file containing the template context.",
        )
        parser.add_argument(
            "--output",
            "-o",
            dest="output",
            type=str,
            default=_DEFAULT_OUTPUT,
            help=f"Path for the output preview HTML file (default: {_DEFAULT_OUTPUT}).",
        )
        parser.add_argument(
            "--open",
            dest="open_browser",
            action="store_true",
            default=False,
            help="Open the written preview file in the system default browser.",
        )
        parser.add_argument(
            "--part",
            dest="part",
            choices=_PART_CHOICES,
            default="all",
            help=(
                "Which part to output. 'all' writes the full tri-pane preview file; "
                "any other value prints only that part to stdout."
            ),
        )
        parser.add_argument(
            "--watch",
            dest="watch",
            action="store_true",
            default=False,
            help="Re-render the preview whenever the template file's mtime changes.",
        )

    def _load_context(self, context_inline: str | None, context_file: str | None) -> dict:
        """Resolve the template context from inline JSON or a JSON file.

        Inline JSON (``--context``) takes precedence when both are supplied.

        Args:
            context_inline: Raw JSON string passed via ``--context``, or ``None``.
            context_file: Filesystem path to a JSON file passed via ``--context-file``, or ``None``.

        Returns:
            A dict representing the template context. Returns ``{}`` when neither
            argument is supplied.

        Raises:
            CommandError: If the supplied JSON is invalid or the context file cannot be read.
        """
        if context_inline is not None:
            try:
                parsed = json.loads(context_inline)
            except json.JSONDecodeError as exc:
                raise CommandError(f"Invalid JSON passed to --context: {exc}") from exc
            if not isinstance(parsed, dict):
                raise CommandError(f"Context must be a JSON object (got {type(parsed).__name__}).")
            return parsed

        if context_file is not None:
            try:
                with open(context_file, encoding="utf-8") as fh:
                    parsed = json.load(fh)
            except (OSError, json.JSONDecodeError) as exc:
                raise CommandError(f"Could not read --context-file {context_file!r}: {exc}") from exc
            if not isinstance(parsed, dict):
                raise CommandError(f"Context must be a JSON object (got {type(parsed).__name__}).")
            return parsed

        return {}

    def _render(self, backend: MarkdownTemplateBackend, template_name: str, context: dict) -> dict:
        """Render the template and return the email parts dict.

        Args:
            backend: An instantiated ``MarkdownTemplateBackend``.
            template_name: Template name (without extension) to render.
            context: Dict of template variables.

        Returns:
            Dict with keys ``html``, ``plain``, ``subject``, and ``preheader``.

        Raises:
            CommandError: If the template cannot be found.
        """
        try:
            return backend._render_email(template_name, context)
        except TemplateDoesNotExist as exc:
            raise CommandError(
                f"Template {template_name!r} not found. " "Ensure TEMPLATED_EMAIL_TEMPLATE_DIR is configured correctly."
            ) from exc

    def _resolve_template_path(self, backend: MarkdownTemplateBackend, template_name: str) -> str | None:
        """Attempt to resolve the filesystem path for a template.

        Used by ``--watch`` to obtain the file path for mtime polling. Returns
        ``None`` when the path cannot be determined (watch mode degrades gracefully).

        Args:
            backend: An instantiated ``MarkdownTemplateBackend``.
            template_name: Template name (without extension).

        Returns:
            Absolute filesystem path string, or ``None`` if unresolvable.
        """
        from django.template.loader import get_template

        # NOTE: template_prefix and template_suffix are implementation details of the
        # parent django-templated-email TemplateBackend class. No public API exists for
        # resolving the on-disk path of a template, so we access these private attributes
        # directly. getattr() with defaults ensures we degrade gracefully (return None)
        # if the attributes are ever renamed or removed in a future library version.
        suffix = getattr(backend, "template_suffix", "md")
        template_dir = getattr(backend, "template_prefix", "templated_email/") or "templated_email/"
        full_name = f"{template_dir}{template_name}.{suffix}"
        try:
            tpl = get_template(full_name)
            origin = tpl.origin
            return origin.name if origin else None
        except Exception:
            return None

    def handle(self, *args, **options):
        """Execute the preview_email command.

        Args:
            args: Positional arguments (unused by this command).
            options: Parsed options dict from argparse, including ``template_name``,
                ``context_inline``, ``context_file``, ``output``, ``open_browser``,
                ``part``, and ``watch``.
        """
        template_name: str = options["template_name"]
        context_inline: str | None = options["context_inline"]
        context_file: str | None = options["context_file"]
        output_path: str = options["output"]
        open_browser: bool = options["open_browser"]
        part: str = options["part"]
        watch: bool = options["watch"]

        context = self._load_context(context_inline, context_file)
        backend = MarkdownTemplateBackend()

        # Render once (validates the template exists before entering any loop)
        result = self._render(backend, template_name, context)

        if part != "all":
            if watch:
                self.stderr.write(self.style.WARNING("--watch is ignored when --part is set."))
            self.stdout.write(result[part])
            return

        self._write_preview(result, output_path, open_browser)

        if watch:
            self._watch_loop(backend, template_name, context, output_path)

    def _write_preview(self, result: dict, output_path: str, open_browser: bool) -> None:
        """Build and write the tri-pane preview HTML to ``output_path``.

        Args:
            result: Dict with keys ``html``, ``plain``, ``subject``, ``preheader``.
            output_path: Destination file path.
            open_browser: When ``True``, open the file in the system browser after writing.
        """
        page = build_preview_page(
            subject=result["subject"],
            preheader=result["preheader"],
            html_body=result["html"],
            plain=result["plain"],
        )
        abs_path = os.path.abspath(output_path)
        Path(abs_path).write_text(page, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Preview written to: {abs_path}"))
        if open_browser:
            webbrowser.open(f"file://{abs_path}")

    def _watch_loop(
        self,
        backend: MarkdownTemplateBackend,
        template_name: str,
        context: dict,
        output_path: str,
    ) -> None:
        """Poll the template file for mtime changes and re-render on each change.

        Runs an infinite loop (until interrupted with Ctrl-C) that sleeps for
        ``_WATCH_INTERVAL_SECONDS`` between checks.

        Args:
            backend: An instantiated ``MarkdownTemplateBackend``.
            template_name: Template name (without extension).
            context: Dict of template variables.
            output_path: Destination file path for the preview.
        """
        import time

        tpl_path = self._resolve_template_path(backend, template_name)
        if tpl_path is None:
            self.stderr.write(
                self.style.WARNING("Could not resolve template path for --watch; " "file-change detection unavailable.")
            )
            return

        last_mtime = os.stat(tpl_path).st_mtime
        self.stdout.write(self.style.WARNING(f"Watching {tpl_path} for changes... (Ctrl-C to stop)"))

        try:
            while True:
                time.sleep(_WATCH_INTERVAL_SECONDS)
                changed, last_mtime = file_changed(tpl_path, last_mtime)
                if changed:
                    self.stdout.write("Template changed - re-rendering...")
                    try:
                        result = self._render(backend, template_name, context)
                        self._write_preview(result, output_path, open_browser=False)
                    except CommandError as exc:
                        self.stderr.write(self.style.ERROR(f"Render error: {exc}"))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("Watch mode stopped."))
