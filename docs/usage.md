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

```markdown
{% block subject %}Welcome to Our Service{% endblock %}

{% block preheader %}Thanks for signing up!{% endblock %}

{% block content %}
# Welcome, {{ user.first_name }}!

We're thrilled to have you join our service. Here are a few things you can do to get started:

1. **Complete your profile**
2. **Explore our features**
3. **Connect with other users**

If you have any questions, don't hesitate to reach out to our support team.

Best regards,
The Team
{% endblock %}
```

### Template Blocks

- **subject**: Defines the email subject line.
- **preheader** *(optional)*: A short summary text that follows the subject line when viewing the email in an inbox.
- **content**: The main content of your email.

### Using Django Template Syntax

You can use Django's template language within your Markdown templates to make each email dynamic.

## Sending Emails

Use the `send_templated_mail` function from `django-templated-email` to send emails using your Markdown templates:

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

#### Example: `templated_email/markdown_base.html`

```html
{% load i18n %}<!DOCTYPE html>
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

Update the `TEMPLATED_EMAIL_BASE_HTML_TEMPLATE` setting if you use a custom template:

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

## Edge Cases and Considerations

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
