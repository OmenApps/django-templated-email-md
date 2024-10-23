# django-templated-email-md

[![PyPI](https://img.shields.io/pypi/v/django-templated-email-md.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/django-templated-email-md.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/django-templated-email-md)][pypi status]
[![License](https://img.shields.io/pypi/l/django-templated-email-md)][license]

[![Read the documentation at https://django-templated-email-md.readthedocs.io/](https://img.shields.io/readthedocs/django-templated-email-md/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/OmenApps/django-templated-email-md/actions/workflows/tests.yml/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/OmenApps/django-templated-email-md/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/django-templated-email-md/
[read the docs]: https://django-templated-email-md.readthedocs.io/
[tests]: https://github.com/OmenApps/django-templated-email-md/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/OmenApps/django-templated-email-md
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

- **Markdown Templates**: Write email templates using Markdown syntax for cleaner and more readable templates.
- **Automatic Conversion**: Automatically converts Markdown to HTML and generates a plain text version of emails.
- **CSS Inlining**: Inlines CSS styles for better email client compatibility using Premailer.
- **Seamless Integration**: Works as an extension of `django-templated-email`, allowing for easy integration into existing projects.
- **Template Inheritance**: Supports Django template inheritance and template tags in your Markdown templates.

## Installation

You can install `django-templated-email-md` via [pip] from [PyPI]:

```bash
pip install django-templated-email-md
```

### Add to `INSTALLED_APPS`

Add `templated_email_md` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'templated_email_md',
    # ...
]
```

## Configuration

Assuming you have already installed and configured [django-templated-email](https://github.com/vintasoftware/django-templated-email/), update your Django settings as follows:

```python
# settings.py

# Configure the templated email backend
TEMPLATED_EMAIL_BACKEND = 'templated_email_md.backend.MarkdownTemplateBackend'

# Optional: Specify the base HTML template for wrapping your content. See the Usage guide for details.
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

## Usage

### Creating Markdown Templates

Place your Markdown email templates in the `templated_email/` directory within your project's templates directory. For example, create a file `templated_email/welcome.md`:

```markdown
{% block subject %}Test Email{% endblock %}
{% block preheader %}Thanks for signing up!{% endblock %}

{% block content %}
# {{ user.first_name }}, you're in!

![Gorgeous, golden potato, Spedona, CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0, via Wikimedia Commons](https://upload.wikimedia.org/wikipedia/commons/a/a4/Icone_pdt.png)

## Welcome to The Potato Shop

### Hello {{ user.fiest_name }}! 👋

> You have been invited to set up an account at the Potato shop on behalf of  **{{ inviter.name }}**.

Please click [this link]({% url 'invitations:accept-invite' key=invitation.key %}) to establish your account.

{% blocktranslate %}You will be directed to the 'set password' tool, where you can establish your account password.{% endblocktranslate %}

---

Best regards,

*Jack Linke*
Potato Shop, LLC - Managing Director

*Semi-round, Starchy Veggies for All*
{% endblock %}
```

### Sending Emails

Use the `send_templated_mail` function to send emails using your Markdown templates, just as you would with the base django-templated-email package:

```python
from templated_email import send_templated_mail

send_templated_mail(
    template_name='welcome',
    from_email='Potato Shop Support <support@mashedupyum.com>',
    recipient_list=['terrence3725fries@wannamashitup.com'],
    context={
        'user': request.user,
        'inviter': inviter,
    },
)
```

### The Result

![Email Preview](https://raw.githubusercontent.com/OmenApps/django-templated-email-md/0495a02b8f4a6affebefb3c2e89562c553851b17/docs/_static/email_screenshot.png)

More detailed information can be found in the [usage guide][usage guide].

## Documentation

For more detailed information, please refer to the [full documentation][read the docs].

## Contributing

Contributions are very welcome. To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license], `django-templated-email-md` is free and open source software.

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

## Credits

We are grateful to the maintainers of the following projects:

- [django-templated-email](https://github.com/vintasoftware/django-templated-email/)
- [emark](https://github.com/voiio/emark)

This project was generated from [@OmenApps]'s [Cookiecutter Django Package] template.

[@omenapps]: https://github.com/OmenApps
[pypi]: https://pypi.org/
[license]: https://github.com/OmenApps/django-templated-email-md/blob/main/LICENSE
[read the docs]: https://django-templated-email-md.readthedocs.io/
[usage guide]: https://django-templated-email-md.readthedocs.io/en/latest/usage.html
[contributor guide]: https://github.com/OmenApps/django-templated-email-md/blob/main/CONTRIBUTING.md
[file an issue]: https://github.com/OmenApps/django-templated-email-md/issues
[cookiecutter django package]: https://github.com/OmenApps/cookiecutter-django-package
[pip]: https://pip.pypa.io/
