
# Settings Guide

There are several settings available to ensure `django-templated-email-md` can be configured for your needs.

The only one that is **required** is `TEMPLATED_EMAIL_BACKEND`.

## Core Settings

### `TEMPLATED_EMAIL_BACKEND`
- **Default:** None
- **Required:** Yes
- **Type:** String
- **Description:** The backend class to use for processing Markdown email templates.
- **Example:**
```python
TEMPLATED_EMAIL_BACKEND = 'templated_email_md.backend.MarkdownTemplateBackend'
```

### `TEMPLATED_EMAIL_TEMPLATE_DIR`
- **Default:** 'templated_email/'
- **Required:** No
- **Type:** String
- **Description:** Directory where email templates are stored. Must include a trailing slash. This is set by default in the `django-templated-email` package.
- **Example:**
```python
TEMPLATED_EMAIL_TEMPLATE_DIR = 'templated_email/'
```
- **Further Reading:** [Django Template Loading Documentation](https://docs.djangoproject.com/en/stable/topics/templates/#template-loading)

### `TEMPLATED_EMAIL_FILE_EXTENSION`
- **Default:** 'md'
- **Required:** No
- **Type:** String
- **Description:** File extension for Markdown template files.
- **Example:**
```python
TEMPLATED_EMAIL_FILE_EXTENSION = 'md'
```

### `TEMPLATED_EMAIL_BASE_HTML_TEMPLATE`
- **Default:** 'templated_email/markdown_base.html'
- **Required:** No
- **Type:** String
- **Description:** Path to the base HTML template that wraps the Markdown content. See the [usage guide](https://django-templated-email-md.readthedocs.io/en/latest/usage.html) for more information on available approaches to overriding the default template.
- **Example:**
```python
TEMPLATED_EMAIL_BASE_HTML_TEMPLATE = 'my_app/markdown_base.html'
```
- **Further Reading:** [Django Template Inheritance](https://docs.djangoproject.com/en/stable/ref/templates/language/#template-inheritance)

## Markdown Settings

### `TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS`
- **Default:** ['markdown.extensions.extra', 'markdown.extensions.meta', 'markdown.extensions.tables']
- **Required:** No
- **Type:** List
- **Description:** List of Markdown extensions to enable when processing templates.
- **Example:**
```python
TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.meta',
    'markdown.extensions.tables',
    'markdown.extensions.codehilite',
]
```
- **Further Reading:**
  - [Python-Markdown Extensions Documentation](https://python-markdown.github.io/extensions/)
  - Popular extensions:
    - [Extra Extension](https://python-markdown.github.io/extensions/extra/)
    - [Meta Extension](https://python-markdown.github.io/extensions/meta_data/)
    - [Tables Extension](https://python-markdown.github.io/extensions/tables/)

## URL Settings

### `TEMPLATED_EMAIL_BASE_URL`
- **Default:** None
- **Required:** No
- **Type:** String
- **Description:** Base URL to prepend to relative URLs in email templates.
- **Example:**
```python
TEMPLATED_EMAIL_BASE_URL = 'https://example.com'
```
- **Further Reading:**
	- [django-templated-email-md Usage Guide](https://django-templated-email-md.readthedocs.io/en/latest/usage.html)
	- [Django URL Configuration](https://docs.djangoproject.com/en/stable/topics/http/urls/)

## Default Content Settings

### `TEMPLATED_EMAIL_DEFAULT_SUBJECT`
- **Default:** 'Hello!'
- **Required:** No
- **Type:** String
- **Description:** Default subject line used when no subject is provided in the template or context.
- **Example:**
```python
TEMPLATED_EMAIL_DEFAULT_SUBJECT = 'Message from Our Company'
```

### `TEMPLATED_EMAIL_DEFAULT_PREHEADER`
- **Default:** ''
- **Required:** No
- **Type:** String
- **Description:** Default preheader text used when no preheader is provided in the template or context.
- **Example:**
```python
TEMPLATED_EMAIL_DEFAULT_PREHEADER = 'Important information from Our Company'
```
- **Further Reading:** [Email Preheader Best Practices](https://www.litmus.com/blog/the-ultimate-guide-to-preview-text-support/) (referred to in this blog as 'preview text')

## Branding Settings

### `TEMPLATED_EMAIL_BRANDING`
- **Default:** See defaults table below
- **Required:** No
- **Type:** Dictionary
- **Description:** Controls the visual branding of emails rendered by `MarkdownTemplateBackend`. Any keys you provide are merged over the built-in defaults, so you only need to specify the values you want to override. The full set of defaults reproduces the original package styling exactly, ensuring backward compatibility.

**Default values:**

| Key | Default | Description |
|---|---|---|
| `primary_color` | `#3498db` | Button backgrounds and accents |
| `link_color` | `#3498db` | Hyperlink color |
| `heading_color` | `#000000` | Color for h1-h4 headings |
| `text_color` | `#333333` | Body paragraph text color |
| `background_color` | `#f6f6f6` | Page/email background color |
| `container_background` | `#ffffff` | Inner content container background |
| `font_family` | `sans-serif` | Font stack for body and headings |
| `logo_url` | `""` | URL of the logo image; empty = no logo rendered |
| `logo_alt` | `""` | Alt text for the logo image |
| `logo_width` | `"200"` | Width of the logo image in pixels (as a string) |

- **Example:**
```python
TEMPLATED_EMAIL_BRANDING = {
    "primary_color": "#e74c3c",
    "link_color": "#e74c3c",
    "heading_color": "#2c3e50",
    "text_color": "#555555",
    "background_color": "#f0f0f0",
    "container_background": "#ffffff",
    "font_family": "Georgia, serif",
    "logo_url": "https://cdn.example.com/logo.png",
    "logo_alt": "Acme Corp",
    "logo_width": "180",
}
```

> **Tip:** If you only want to change one or two colors, you can set just those keys and all other defaults will be preserved automatically.

## Plain Text Generation Settings

### `TEMPLATED_EMAIL_HTML2TEXT_SETTINGS`
- **Default:** {}
- **Required:** No
- **Type:** Dictionary
- **Description:** Configuration options for html2text when generating plain text versions of emails.
- **Some of the Available Options:**
  - `ignore_links`: Exclude links from plain text output
  - `ignore_images`: Exclude image descriptions
  - `body_width`: Maximum line width before wrapping
  - `ignore_emphasis`: Exclude emphasis markers
  - `mark_code`: Wrap code blocks with backticks
  - `wrap_links`: Wrap URLs in angle brackets
- **Example:**
```python
TEMPLATED_EMAIL_HTML2TEXT_SETTINGS = {
    'ignore_links': False,
    'ignore_images': True,
    'body_width': 0,
    'ignore_emphasis': True,
    'mark_code': False,
    'wrap_links': False,
}
```
- **Further Reading:** [Available html2text Options](https://github.com/Alir3z4/html2text/blob/master/docs/usage.md#available-options)

## Error Handling Settings

### `TEMPLATED_EMAIL_FAIL_SILENTLY`
- **Default:** False
- **Required:** No
- **Type:** Boolean
- **Description:** If True, suppresses exceptions during email rendering and sends fallback email instead.
- **Example:**
```python
TEMPLATED_EMAIL_FAIL_SILENTLY = True
```

## HTML Sanitization Settings

> **Note:** HTML sanitization requires the optional `nh3` dependency. Install it with:
>
> ```bash
> pip install django-templated-email-md[sanitize]
> ```
>
> If `TEMPLATED_EMAIL_SANITIZE = True` but `nh3` is not installed, email sending will
> raise `ImportError` - install the `[sanitize]` extra to resolve it. This error is
> raised even when `TEMPLATED_EMAIL_FAIL_SILENTLY = True`, because silently skipping
> requested sanitization would be a security risk.

### `TEMPLATED_EMAIL_SANITIZE`
- **Default:** `False`
- **Required:** No
- **Type:** Boolean
- **Description:** When `True`, sanitizes the HTML produced from the Markdown `content`
  block before it is wrapped in the base template. Uses the `nh3` library (Python
  bindings for the Rust `ammonia` crate) to strip dangerous constructs such as
  `<script>` tags, event handler attributes (`onclick`, etc.), and `javascript:` URLs.
  Defaults to `False` for full backward compatibility - existing templates are unaffected
  unless you explicitly opt in.

  > **Important caveat:** `nh3`'s default allowlist is conservative. By default it
  > strips `class` attributes and some table/button markup. Sanitization runs on the
  > Markdown `content` fragment before it is wrapped in the base template, so the base
  > template's own classes are never affected - only `class` attributes in raw HTML
  > written directly in your `content` block (e.g. `<div class="foo">` placed inline
  > in the Markdown source) will be stripped. If you use such markup, you must extend
  > the allowlist via `TEMPLATED_EMAIL_SANITIZE_KWARGS`.
  > Users who render fully trusted template markup (e.g. no user-supplied context
  > values reach the content block) may prefer to leave sanitization off.

- **Example:**
```python
TEMPLATED_EMAIL_SANITIZE = True
```

### `TEMPLATED_EMAIL_SANITIZE_KWARGS`
- **Default:** `{}`
- **Required:** No
- **Type:** Dictionary
- **Description:** Keyword arguments passed directly to `nh3.clean()`. Use this to
  extend or restrict the default allowlists. Common keys include:
  - `tags`: `set[str]` - allowed HTML tag names (overrides nh3 default allowlist).
  - `attributes`: `dict[str, set[str]]` - maps tag names to sets of allowed attribute
    names. Note that passing this key overrides nh3's entire default attribute
    allowlist, so include all attributes you need (not just the additions).
  - `url_schemes`: `set[str]` - allowed URL schemes (default includes `http`, `https`,
    `mailto`).

  Refer to the [nh3 documentation](https://nh3.readthedocs.io/) for the full list of
  accepted keyword arguments.

- **Example (allow `class` attribute on all elements):**
```python
TEMPLATED_EMAIL_SANITIZE = True
TEMPLATED_EMAIL_SANITIZE_KWARGS = {
    "attributes": {
        "*": {"class"},
        "a": {"href", "title", "class"},
        "img": {"src", "alt", "class"},
    }
}
```

> **Note:** nh3's DEFAULT allowlist strips most attributes, including `class` and `target`.
> Because sanitization runs on the Markdown-rendered content fragment, this has two
> consequences for the bundled components:
>
> (a) The shipped bulletproof partials (`templated_email/components/button.html` and
> `divider.html`) included from a `content` block will lose their `class="btn btn-primary"` /
> `class="email-divider"` and `target` attributes, so Premailer can no longer style them
> correctly.
>
> (b) Any `class`-based styling written as raw HTML directly in your `content` block
> (e.g. `<div class="foo">`) is also removed.
>
> To keep those attributes, extend the allowlist via `TEMPLATED_EMAIL_SANITIZE_KWARGS`
> (e.g. allow `class` on the relevant tags, as shown in the example above).
>
> **Important interaction with render caching:** nh3 allowlists are typically expressed
> as Python `set`s (e.g. `{"class"}`), and sets are not JSON-serializable. The render
> cache key is built with `json.dumps`, so if `TEMPLATED_EMAIL_SANITIZE_KWARGS` contains
> a set (or any other non-JSON-serializable value), render caching is silently skipped
> for those calls. If you want both sanitization with custom kwargs and caching, be aware
> of this limitation, or express allowlists in a JSON-serializable form where possible.

## Complete Configuration Example

Here's a complete example showing all settings with their default values:

```python
# Email Backend Configuration
TEMPLATED_EMAIL_BACKEND = 'templated_email_md.backend.MarkdownTemplateBackend'
TEMPLATED_EMAIL_TEMPLATE_DIR = 'templated_email/'
TEMPLATED_EMAIL_FILE_EXTENSION = 'md'
TEMPLATED_EMAIL_BASE_HTML_TEMPLATE = 'templated_email/markdown_base.html'

# Markdown Extensions
TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.meta',
    'markdown.extensions.tables',
]

# URL Configuration
TEMPLATED_EMAIL_BASE_URL = ''

# Default Content
TEMPLATED_EMAIL_DEFAULT_SUBJECT = 'Hello!'
TEMPLATED_EMAIL_DEFAULT_PREHEADER = ''

# Plain Text Generation
TEMPLATED_EMAIL_HTML2TEXT_SETTINGS = {
    'ignore_links': False,
    'ignore_images': True,
    'body_width': 0,
    'ignore_emphasis': True,
    'mark_code': False,
    'wrap_links': False,
}

# Error Handling
TEMPLATED_EMAIL_FAIL_SILENTLY = False

# HTML Sanitization (requires: pip install django-templated-email-md[sanitize])
TEMPLATED_EMAIL_SANITIZE = False
TEMPLATED_EMAIL_SANITIZE_KWARGS = {}

# Render Caching
TEMPLATED_EMAIL_CACHE_RENDERED = False
TEMPLATED_EMAIL_CACHE_TIMEOUT = 300
TEMPLATED_EMAIL_CACHE_ALIAS = "default"
```

## Render Caching

The backend can cache the result of the full render pipeline (Markdown to HTML to
CSS inlining to plain text) in Django's cache framework. Caching is **off by
default** to preserve the existing behaviour.

### `TEMPLATED_EMAIL_CACHE_RENDERED`

| Type | Default |
|------|---------|
| `bool` | `False` |

Set to `True` to enable render caching. When enabled, the backend stores the
rendered `{"html", "plain", "subject", "preheader"}` dict in the cache under a
deterministic SHA-256 key. Subsequent renders with identical template name,
context, language, and base URL will be served from the cache, skipping the
expensive `premailer.transform` call.

The cache key incorporates the template name, context, active language, base
URL, and all rendering-relevant settings - markdown extensions, html2text
settings, sanitize flags, and branding. A change to any of these settings
produces a different cache key, so cached HTML is never served after a settings
change.

**Note:** Only contexts and settings whose values are JSON-serializable are
cached. If the context or `TEMPLATED_EMAIL_SANITIZE_KWARGS` contains values
that are not JSON-serializable (e.g. a `set` used as an nh3 allowlist, or a
model instance), caching is skipped for that call and the email is rendered
normally - this is a safe fallback, not an error.

> **Note:** The cache key incorporates the template NAME, context, active language, base
> URL, and rendering-relevant settings (markdown extensions, html2text settings, sanitize
> flags, and branding) - but NOT the template file's contents. If you edit a template
> file without changing any of those inputs, cached output continues to be served until
> the entry expires. After deploying changed templates, either flush the cache (or cycle
> the cache alias) or keep `TEMPLATED_EMAIL_CACHE_TIMEOUT` short relative to your deploy
> cadence.
>
> If the context (or `TEMPLATED_EMAIL_SANITIZE_KWARGS`) contains values that are not
> JSON-serializable, the cache key cannot be computed and caching is safely skipped for
> that call - no error is raised.

### `TEMPLATED_EMAIL_CACHE_TIMEOUT`

| Type | Default |
|------|---------|
| `int` | `300` |

Cache TTL in seconds. Passed directly to Django's `cache.set(key, value,
timeout)`. Set to `None` for a non-expiring entry (if the cache backend
supports it).

### `TEMPLATED_EMAIL_CACHE_ALIAS`

| Type | Default |
|------|---------|
| `str` | `"default"` |

The Django cache alias to use. Must be a key defined in `settings.CACHES`.

### Example

```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}

TEMPLATED_EMAIL_CACHE_RENDERED = True
TEMPLATED_EMAIL_CACHE_TIMEOUT = 600   # 10 minutes
TEMPLATED_EMAIL_CACHE_ALIAS = "default"
```

## Notes

1. To implement any of the above settings, the setting should be added to your Django project's `settings.py` file.
2. Many settings have sensible defaults and are optional.
3. The TEMPLATED_EMAIL_BACKEND setting is required and must be set explicitly.
4. When using relative URLs in templates (either explicitly in the template or when using Django's [url template tags](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#url)), either TEMPLATED_EMAIL_BASE_URL should be set in settings, or base_url should be provided when calling send_templated_mail.

## Additional Resources

- [django-templated-email Documentation](https://github.com/vintasoftware/django-templated-email/)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Django Templates Documentation](https://docs.djangoproject.com/en/stable/topics/templates/)
- [Python-Markdown Documentation](https://python-markdown.github.io/)
