"""Preview helpers for django-templated-email-md.

This module provides utilities for building a self-contained HTML preview of a
rendered email and for detecting template file changes during watch mode.
"""

import html
import os


def build_preview_page(subject: str, preheader: str, html_body: str, plain: str) -> str:
    """Build a self-contained tri-pane HTML preview document.

    Produces a single HTML file that renders the email subject and preheader in a
    header bar, the full HTML email inside an ``<iframe srcdoc>`` (so the email's
    own styles are isolated from the wrapper chrome), and the plain-text version in
    a ``<pre>`` panel.

    The ``html_body`` value is escaped with ``html.escape(value, quote=True)`` before
    being embedded in the ``srcdoc`` attribute to prevent attribute-boundary breakage.

    Args:
        subject: The email subject line.
        preheader: The email preheader / preview text.
        html_body: The fully-rendered HTML email body.
        plain: The plain-text version of the email.

    Returns:
        A complete, self-contained HTML document string starting with ``<!DOCTYPE html>``.
    """
    escaped_html_body = html.escape(html_body, quote=True)
    escaped_plain = html.escape(plain, quote=False)
    srcdoc_attr = "srcdoc=" + '"' + escaped_html_body + '"'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Email Preview: {html.escape(subject, quote=False)}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f0f2f5;
      color: #1a1a2e;
    }}
    #header {{
      background: #1a1a2e;
      color: #fff;
      padding: 16px 24px;
    }}
    #header h1 {{ margin: 0 0 4px; font-size: 1.1rem; }}
    #header p  {{ margin: 0; font-size: 0.85rem; opacity: 0.7; }}
    #panels {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      padding: 16px;
      height: calc(100vh - 72px);
    }}
    .panel {{
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.12);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    .panel-label {{
      padding: 8px 16px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .05em;
      background: #f8f9fa;
      border-bottom: 1px solid #e9ecef;
    }}
    iframe {{
      flex: 1;
      border: none;
      width: 100%;
    }}
    pre {{
      flex: 1;
      margin: 0;
      padding: 16px;
      overflow: auto;
      font-size: 0.85rem;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }}
  </style>
</head>
<body>
  <div id="header">
    <h1>{html.escape(subject, quote=False)}</h1>
    <p>{html.escape(preheader, quote=False)}</p>
  </div>
  <div id="panels">
    <div class="panel">
      <div class="panel-label">HTML Preview</div>
      <iframe {srcdoc_attr} title="HTML email preview"></iframe>
    </div>
    <div class="panel">
      <div class="panel-label">Plain Text</div>
      <pre>{escaped_plain}</pre>
    </div>
  </div>
</body>
</html>"""


def file_changed(path: str, last_mtime: float) -> tuple[bool, float]:
    """Check whether a file's modification time has advanced past a known value.

    Args:
        path: Absolute or relative filesystem path to the file.
        last_mtime: The previously recorded ``os.stat().st_mtime`` value.

    Returns:
        A two-tuple ``(changed, current_mtime)`` where ``changed`` is ``True`` when
        the file's current mtime is strictly greater than ``last_mtime``, and
        ``current_mtime`` is the file's actual current mtime.
    """
    current_mtime = os.stat(path).st_mtime
    return current_mtime > last_mtime, current_mtime
