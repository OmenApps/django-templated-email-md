# Usage Guide

## Installation

To install `django-templated-email-md`, run the following command:

```bash
pip install django-templated-email-md
```

## Configuration

### 1. Add to `INSTALLED_APPS`

Add `templated_email_md` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'templated_email_md',
    # ...
]
```

### 2. Update Settings

Assuming you have already installed and configured [django-templated-email](https://github.com/vintasoftware/django-templated-email/), update your Django settings as follows:

```python
# settings.py

# Configure the templated email backend
TEMPLATED_EMAIL_BACKEND = 'templated_email_md.backend.MarkdownTemplateBackend'

# Specify the base HTML template for wrapping your content
TEMPLATED_EMAIL_BASE_HTML_TEMPLATE = 'templated_email/markdown_base.html'

# Set the directory where your email templates are stored
TEMPLATED_EMAIL_TEMPLATE_DIR = 'templated_email/'  # Ensure there's a trailing slash

# Define the file extension for your Markdown templates
TEMPLATED_EMAIL_FILE_EXTENSION = 'md'

# Optional: Specify Markdown extensions if needed
TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.meta',
    'markdown.extensions.tables',
]
```

### 3. Ensure Template Loaders Include `APP_DIRS`

Make sure that your `TEMPLATES` setting includes `APP_DIRS` set to `True` or includes the `django.template.loaders.app_directories.Loader`:

```python
# settings.py

TEMPLATES = [
    {
        # ...
        'APP_DIRS': True,
        # ...
    },
]
```

## Creating Markdown Templates

Place your Markdown email templates in the `templated_email/` directory within your project's templates directory or within an app's `templates` directory.

### Example Template: `templated_email/welcome.md`

*Note: The subject and preheader can be provided as template blocks or as context arguments when sending email.*

```markdown
{% load i18n %}

{% block subject %}{% trans "Welcome to Our Service" %}{% endblock %}

{% block preheader %}{% trans "Thanks for signing up!" %}{% endblock %}

{% block content %}
# {% trans "Welcome" %}, {{ user.first_name }}!

{% trans "We're thrilled to have you join our service. Here are a few things you can do to get started:" %}

1. **{% trans "Complete your profile" %}**
2. **{% trans "Explore our features" %}**
3. **{% trans "Connect with other users" %}**

{% trans "If you have any questions, don't hesitate to reach out to our support team." %}

{% trans "Best regards," %}
{% trans "The Team" %}
{% endblock %}
```

### Template Blocks

- **subject**: Defines the email subject line.
- **preheader** *(optional)*: A short summary text that follows the subject line when viewing the email in an inbox.
- **content**: The main content of your email.

### Using Django Template Syntax

You can use Django's template language within your Markdown templates to make each email dynamic.

## Sending Emails

Use the [`send_templated_mail`](https://github.com/vintasoftware/django-templated-email/?tab=readme-ov-file#sending-templated-emails) function from `django-templated-email` to send emails using your Markdown templates:

```python
from templated_email import send_templated_mail

send_templated_mail(
    template_name='welcome',
    from_email='from@example.com',
    recipient_list=['to@example.com'],
    context={
        'user': user_instance,
        # Add other context variables as needed
    },
)
```

*Remember to provide all necessary context variables when sending the email.*

### Important Notes

- **Context Variables**: Ensure that all variables used in your templates are provided in the `context` dictionary.
- **Template Name**: Do not include the file extension when specifying the `template_name`.

## Advanced Usage

### Custom Base Template

While we recommend you stick with the provided base template, you can create a custom base HTML template to wrap your Markdown content.
This allows you to define the overall structure and style of your emails.

There are two ways to achieve this:

1. **Template Overrides**: Within the `templates/` directory in your project's base directory, create a `templated_email/` directory. Then add a `markdown_base.html` file to serve as the base template. This will override the default base template from the package.
2. **Custom Base Template**: Place your custom base HTML template elsewhere and update the `TEMPLATED_EMAIL_BASE_HTML_TEMPLATE` setting to point to it.

#### Example: `templated_email/markdown_base.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ subject }}</title>
    <style>
        /* Include your CSS styles here */
    </style>
</head>
<body>
    {% spaceless %}
        {% block content %}{{ markdown_content|safe }}{% endblock %}
    {% endspaceless %}
</body>
</html>
```

Update the `TEMPLATED_EMAIL_BASE_HTML_TEMPLATE` setting if you use a custom template in a different location:

```python
TEMPLATED_EMAIL_BASE_HTML_TEMPLATE = 'templated_email/markdown_base.html'
```

### Inline Styles

The `MarkdownTemplateBackend` uses Premailer to inline CSS styles for better email client compatibility.

- **Include `<style>` Tags**: Place your CSS styles within `<style>` tags in your base HTML template.
- **External CSS Files**: External CSS files are not recommended for emails due to limited support in email clients.

### Plain Text Version

A plain text version of your email is automatically generated using `html2text`.

- **Customization**: If you need to customize the plain text output, you can override the `_generate_plain_text` method in a subclass of `MarkdownTemplateBackend`.
- **Links and Formatting**: By default, links are preserved, and markdown formatting is converted to plain text.

### Template Inheritance

You can leverage Django's template inheritance in your Markdown templates.

#### Base Template: `templated_email/base_email.md`

```markdown
{% block subject %}Default Subject{% endblock %}

{% block preheader %}Default Preheader{% endblock %}

{% block content %}
Default content.
{% endblock %}
```

#### Child Template: `templated_email/custom_email.md`

```markdown
{% extends "templated_email/base_email.md" %}

{% block subject %}Custom Email Subject{% endblock %}

{% block content %}
# Custom Content

This is a custom email.
{% endblock %}
```

### Using Django Template Tags and Filters

Your Markdown templates can include Django's template tags and filters.

#### Example with Logic and Filters

```markdown
{% block content %}
{% if user.is_premium %}
# Welcome, Premium User!

Thank you for subscribing to our premium service.

{% else %}
# Welcome!

Consider upgrading to our premium service for more benefits.
{% endif %}

Your username is: **{{ user.username|lower }}**
{% endblock %}
```

### Internationalization (i18n) and Translated Emails

To send emails in different languages using internationalization (i18n), you need to:

1. **Use Translation Tags in Templates**: Wrap translatable text in `trans` or `blocktrans` tags.
2. **Set Up Translation Files**: Generate and compile message files for each language.
3. **Activate the Desired Language**: Use `translation.override(language_code)` when sending the email.
4. **Ensure Thread Safety with Celery**: Activate the language within the task function if using asynchronous tasks.

#### 1. Use Translation Tags in Your Templates

Include the `{% load i18n %}` tag and wrap text for translation.

```markdown
{% load i18n %}

{% block subject %}{% trans "Welcome to Our Service" %}{% endblock %}

{% block preheader %}{% trans "Thanks for signing up!" %}{% endblock %}

{% block content %}
# {% trans "Welcome" %}, {{ user.first_name }}!

{% trans "We're thrilled to have you join our service. Here are a few things you can do to get started:" %}

1. **{% trans "Complete your profile" %}**
2. **{% trans "Explore our features" %}**
3. **{% trans "Connect with other users" %}**

{% trans "If you have any questions, don't hesitate to reach out to our support team." %}

{% trans "Best regards," %}
{% trans "The Team" %}
{% endblock %}
```

#### 2. Set Up and Compile Translation Files

Use Django's `makemessages` and `compilemessages` commands.

*Note, to include the ".md" files, you may need to add the `--extension md` or `-e md` flag.*

```bash
# For Spanish translations of Markdown files
django-admin makemessages -l es -e md
# After translating the strings in locale/es/LC_MESSAGES/django.po
django-admin compilemessages
```

#### 3. Activate the Desired Language When Sending the Email

Use `translation.override(language_code)` to temporarily set the language.

```python
from templated_email import send_templated_mail
from django.utils import translation

def send_translated_email(user):
    # Assume user.preferred_language contains the language code, e.g., 'es' for Spanish
    language_code = user.preferred_language

    # Activate the desired language
    with translation.override(language_code):
        send_templated_mail(
            template_name='welcome',
            from_email='from@example.com',
            recipient_list=[user.email],
            context={
                'user': user,
                # Add other context variables as needed
            },
        )
```

#### 4. Using Celery for Asynchronous Email Sending

When sending emails asynchronously with Celery, activate the language within the task function to ensure thread safety.

```python
from celery import shared_task
from templated_email import send_templated_mail
from django.utils import translation
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def send_translated_email_task(user_id):
    user = User.objects.get(id=user_id)
    language_code = user.preferred_language

    with translation.override(language_code):
        send_templated_mail(
            template_name='welcome',
            from_email='from@example.com',
            recipient_list=[user.email],
            context={
                'user': user,
            },
        )
```

#### 5. Handle Fallback Languages

Optionally, provide a default language if the user's preferred language is not supported.

```python
supported_languages = ['en', 'es', 'fr']  # List of supported language codes
language_code = user.preferred_language if user.preferred_language in supported_languages else 'en'

with translation.override(language_code):
    # Send email as before
```

#### Additional Considerations

- **Load the `i18n` Template Tag Library**: Include `{% load i18n %}` at the top of your templates.
- **Use `blocktrans` for Blocks of Text**: Use `{% blocktrans %}` when translating longer blocks that may include variables.
- **Keep Translations Updated**: Whenever you change text in your templates or code, regenerate and recompile your message files.
- **Provide Translations for All Strings**: Ensure all strings in templates and code are marked for translation.

## Edge Cases and Considerations

### Default Subject and Preheader

- **Providing Defaults**: If the `subject` and `preheader` blocks are not defined in the template, the default values are used.
- **Customizing Defaults**: You can set default values for the subject and preheader in the context when sending the email.

#### Settings

You can also set default values for the subject and preheader in your Django settings. These are used if a value is not provided
in the template or context, or if you have set `fail_silently` to `True` and an error occurs.

```python
TEMPLATED_EMAIL_DEFAULT_SUBJECT = 'Default Subject'
TEMPLATED_EMAIL_DEFAULT_PREHEADER = 'Default Preheader'
```

If not set, the default value for subject is `'Hello!'` and for preheader is `''`.

### Subject Overriding

- **From Context**: You can override the subject by providing a `subject` key in the context.
- **Priority**: The `subject` in the context takes precedence over the one defined in the template.

#### Example

```python
send_templated_mail(
    template_name='welcome',
    from_email='from@example.com',
    recipient_list=['to@example.com'],
    context={
        'user': user_instance,
        'subject': 'Custom Subject Line',
    },
)
```

### URL Template Tags and Relative URLs

In order to include URLs in your emails, you can use Django's URL template tags or pass the URL as a context variable.

In either case, to transform relative URLs into absolute URLs, you can set the `TEMPLATED_EMAIL_BASE_URL` setting in your Django
settings, or for more flexibility, you can add a `base_url` argument to the `send_templated_mail` function. This will be used to
prepend relative URLs in your email templates.

#### Example

```python
send_templated_mail(
    template_name='welcome',
    from_email="from@example.com",
        recipient_list=["to@example.com"],
        context={
            "user": user_instance,
        },
        base_url="http://example.com",
    )
```

### Code and code blocks

When working with templates that include code snippets that should be rendered verbatim in the resulting email combined with Django template tags, the Django template engine will attempt to interpret and render these tags, which can lead to errors or unintended behavior.

This section applies to all of the following examples:

```markdown
    <code>{% url %}</code>

    <code>{{ url }}</code>

    `{% url %}`

    `{{ url }}`

    ```html
    {% url %}
    ```

    ```html
    {{ url }}
    ```
```

To prevent django-templated-email-md from processing the content inside code blocks, you can wrap the relevant content with Django's built-in [`{% verbatim %}` template tag](https://docs.djangoproject.com/en/5.1/ref/templates/builtins/#verbatim).

#### Example

```markdown
{% block content %}
    Here is some code:

    {% verbatim %}
    <code>{% url %}</code>
    {% endverbatim %}

    Another code snippet:

    {% verbatim %}
    `{{ url }}`
    {% endverbatim %}

    And a code block:

    {% verbatim %}
    ```python
    {{ url }
    ```
    {% endverbatim %}

    More content here.
{% endblock %}
```


### Context Variables

- **Missing Variables**: If a variable used in the template is missing from the context, the email rendering will fail unless `fail_silently` is set to `True`.
- **Providing All Variables**: Ensure all variables and conditions in your templates are accounted for in the context.

### Markdown Extensions

- **Default Extensions**: The backend uses a set of default Markdown extensions.
- **Customization**: You can customize the Markdown extensions via the `TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS` setting.

#### Example

```python
TEMPLATED_EMAIL_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.codehilite',
]
```

### Customizing Plain Text Generation

The `MarkdownTemplateBackend` uses `html2text` to automatically generate the plain text version of your emails from the HTML content. By default, certain configurations are set to produce a clean plain text output. However, you can override these settings to fit your specific needs.

#### **Available `html2text` Settings**

You can customize the behavior of `html2text` by specifying settings in your `settings.py` file using the `TEMPLATED_EMAIL_HTML2TEXT_SETTINGS` dictionary. Some common settings include:

- `ignore_links`: If `True`, links will not be included in the plain text.
- `ignore_images`: If `True`, image descriptions will be ignored.
- `body_width`: Sets the maximum width of the text before wrapping.
- `ignore_emphasis`: If `True`, emphasis markers (`*`, `**`) will be ignored.
- `mark_code`: If `True`, code blocks will be wrapped with backticks.
- `wrap_links`: If `True`, URLs will be wrapped in angle brackets (`<`, `>`).
- `use_automatic_links`: If `True`, links will be converted to a simpler format.

For a full list of settings, refer to the [html2text documentation](https://github.com/Alir3z4/html2text/blob/master/docs/usage.md#available-options). For any setting you want to configure, use the lowercase version of the setting name as the key in the `TEMPLATED_EMAIL_HTML2TEXT_SETTINGS` dictionary.

#### **Example `html2text` Configuration**

```python
# settings.py

TEMPLATED_EMAIL_HTML2TEXT_SETTINGS = {
    'ignore_links': True,
    'ignore_images': False,
    'body_width': 80,
    'ignore_emphasis': False,
    'mark_code': True,
    'wrap_links': True,
}
```

### Error Handling

- **fail_silently**: Set this option to `True` to suppress exceptions during email rendering and send a fallback email instead.
- **Logging**: Errors are logged using Django's logging framework.

#### Example

```python
# settings.py

TEMPLATED_EMAIL_BACKEND = 'templated_email_md.backend.MarkdownTemplateBackend'
TEMPLATED_EMAIL_FAIL_SILENTLY = True
```

## Examples

### Sending an Email with Attachments

```python
from templated_email import send_templated_mail

send_templated_mail(
    template_name='invoice',
    from_email='billing@example.com',
    recipient_list=['customer@example.com'],
    context={
        'user': user_instance,
        'invoice': invoice_instance,
    },
    attachments=[
        ('invoice.pdf', invoice_pdf_content, 'application/pdf'),
    ],
)
```

## Email Preview Tool

The `preview_email` management command renders any Markdown email template to a
self-contained HTML file without sending an email. It is useful during development
to inspect the final rendered output - including CSS-inlined HTML and plain text -
directly in a browser.

### Basic usage

```bash
python manage.py preview_email welcome_email --context '{"name": "Alice"}' --open
```

This renders `welcome_email.md`, writes `email_preview.html` in the current
directory, and opens it in your default browser.

### Options

| Option | Description |
|---|---|
| `template_name` | Template name (without extension) to render. |
| `--context JSON` | Inline JSON string used as the template context. |
| `--context-file PATH` | Path to a JSON file used as the template context (`--context` wins if both are given). |
| `--output PATH` / `-o PATH` | Output path for the preview file (default: `email_preview.html`). |
| `--open` | Open the written file in the system default browser. |
| `--part PART` | Print only one part to stdout: `html`, `plain`, `subject`, or `preheader`. |
| `--watch` | Re-render automatically whenever the template file changes (Ctrl-C to stop). Watch mode detects changes to the named template file only - it does not detect edits to the base HTML template, the stylesheet, or included component partials; re-run the command (or touch the template file) to pick those up. |

### Print a single part

```bash
# Print just the subject line
python manage.py preview_email welcome_email --context '{"name": "Alice"}' --part subject

# Print the plain-text version
python manage.py preview_email welcome_email --context '{"name": "Alice"}' --part plain
```

### Watch mode

```bash
python manage.py preview_email welcome_email --context '{"name": "Alice"}' --output preview.html --watch
```

The command polls the template file for changes every second and re-renders
whenever its modification time advances. Keep a browser tab open to `preview.html`
and refresh it manually (or use a live-reload browser extension) to see updates.

## Components

The package ships reusable HTML component partials that can be included from within any
Markdown email template's `{% block content %}`. Because Django's template engine resolves
`{% include %}` tags before the Markdown renderer runs, block-level HTML emitted by a
component partial (separated from surrounding text by blank lines) passes through
`markdown.markdown()` unchanged and appears correctly in the final email HTML.

### Button

The `button.html` partial renders a bulletproof, table-based button styled
with the existing `.btn` / `.btn-primary` classes. Pass `url` and `label` via `with`:

```django
{% block content %}
Please confirm your account by clicking the button below.

{% include "templated_email/components/button.html" with url="https://example.com/confirm/abc123" label="Confirm Account" %}

If you did not create an account, you can ignore this email.
{% endblock %}
```

The blank lines before and after the `{% include %}` tag are required - they tell the
Markdown parser to treat the emitted HTML as a block-level element and leave it untouched.

### Divider

The `divider.html` partial renders a full-width horizontal rule using a table row with an
inline `border-bottom` style, which renders reliably across all major email clients:

```django
{% block content %}
This is the first section of the email.

{% include "templated_email/components/divider.html" %}

This is the second section of the email.
{% endblock %}
```

### Customising Components

To override a shipped component, copy the partial from
`src/templated_email_md/templates/templated_email/components/` into your own app's
`templates/templated_email/components/` directory (ensuring your app is listed before
`templated_email_md` in `INSTALLED_APPS`) and modify it as needed.

## Async Sending

`MarkdownTemplateBackend` provides an `asend` coroutine method that wraps the
synchronous `send` in a thread via `asgiref.sync.sync_to_async`. This lets you
await email sending from async Django views, ASGI middleware, or async task
queues without blocking the event loop.

```python
# views.py (async view)
from templated_email_md.backend import MarkdownTemplateBackend

async def welcome_view(request):
    backend = MarkdownTemplateBackend()
    await backend.asend(
        template_name="welcome",
        from_email="hello@example.com",
        recipient_list=[request.user.email],
        context={"user": request.user},
    )
    ...
```

`asend` accepts exactly the same arguments as `send`. The full render pipeline
(Markdown conversion, CSS inlining, plain text generation) and SMTP delivery run
in a thread pool managed by `asgiref`, so the async event loop is never blocked.

> **Note:** `asend` is a thin wrapper - it does not add async-native SMTP
> support. For high-throughput async email delivery, consider a task queue such
> as Celery or Django-Q with `asend` as the async entry point.

> **Note:** `asend` offloads a single blocking send off the event loop, but it
> runs thread-sensitively (to stay safe with ORM writes such as when
> `create_link=True` is used). As a result, many concurrent `asend` calls execute
> one at a time rather than in parallel. For high-volume fan-out to many recipients,
> a task queue (Celery, Django-Q, etc.) is the recommended approach.
