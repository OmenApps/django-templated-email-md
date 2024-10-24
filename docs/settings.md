
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
- **Further Reading:** [Email Preheader Best Practices](https://www.litmus.com/blog/the-ultimate-guide-to-preview-text-support/) (refered to in this blocg as 'preview text')

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
