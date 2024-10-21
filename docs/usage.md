# Usage

## Installation

To install django-templated-email-md, run the following command:

```bash
pip install django-templated-email-md
```

## Configuration

1. Configure the backend in your Django settings:

```python
TEMPLATED_EMAIL_BACKEND = 'templated_email_md.backend.MarkdownTemplateBackend'
TEMPLATED_EMAIL_BASE_HTML_TEMPLATE = 'templated_email/markdown_base.html'
TEMPLATED_EMAIL_TEMPLATE_DIR = 'templated_email/'  # Ensure there's a trailing slash
TEMPLATED_EMAIL_FILE_EXTENSION = 'md'
```

## Creating Markdown Templates

Create your Markdown email templates in the `templated_email/` directory. For example, create a file `templated_email/welcome.md`:

```markdown
{% block subject %}Welcome to Our Service{% endblock %}

{% block preheader %}Thanks for signing up!{% endblock %}

# Welcome, {{ user.first_name }}!

We're thrilled to have you join our service. Here are a few things you can do to get started:

1. **Complete your profile**
2. **Explore our features**
3. **Connect with other users**

If you have any questions, don't hesitate to reach out to our support team.

Best regards,
The Team
```

## Sending Emails

To send an email using your Markdown template:

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

## Advanced Usage

### Custom Base Template

We recommend using the provided base template, but you can also create a custom base HTML template to wrap your Markdown content. Place it in your templates directory and update the `TEMPLATED_EMAIL_BASE_HTML_TEMPLATE` setting.

### Inline Styles

The MarkdownTemplateBackend uses Premailer to inline CSS styles. You can include a `<style>` tag in your base HTML template or link to an external CSS file.

### Plain Text Version

A plain text version of your email is automatically generated using html2text. You don't need to create a separate plain text template.

### Template Inheritance

You can use Django's template inheritance in your Markdown templates. For example:

```markdown
{% extends "base_email.md" %}

{% block content %}
Your specific email content here
{% endblock %}
```

### Using Django Template Tags and Filters

You can use Django template tags and filters in your Markdown templates:

```markdown
{% if user.is_premium %}
## Premium Features

As a premium user, you have access to:

{% for feature in premium_features %}
- {{ feature|title }}
{% endfor %}
{% endif %}
```

Remember to provide all necessary context variables when sending the email.
