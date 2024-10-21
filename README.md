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

- Write email templates using Markdown syntax
- Automatically converts Markdown to HTML
- Generates plain text version of emails
- Inlines CSS styles for better email client compatibility
- Seamless integration with django-templated-email
- Supports Django template inheritance and tags

## Dependencies

- Django (>=4.2)
- django-templated-email (~=3.0)
- markdown (~=3.7)
- premailer (~=3.10)
- html2text (~=2024.2)

## Installation

You can install _django-templated-email-md_ via [pip] from [PyPI]:

```console
$ pip install templated_email_md
```

## Usage

**Usage Instructions:**

1. **Update Your Settings:**

   *Assumes you have already installed and configured [django-templated-email](https://github.com/vintasoftware/django-templated-email/).*

   Add or update the following in your Django `settings.py`:

   ```python
   TEMPLATED_EMAIL_BACKEND = 'templated_email_md.backend.MarkdownTemplateBackend'
   TEMPLATED_EMAIL_BASE_HTML_TEMPLATE = 'templated_email/markdown_base.html'
   TEMPLATED_EMAIL_TEMPLATE_DIR = 'templated_email/'  # Ensure there's a trailing slash
   TEMPLATED_EMAIL_FILE_EXTENSION = 'md'
   ```

2. **Create Your Markdown Email Templates:**

   Place your Markdown email templates in the `templated_email/` directory. For example, create a file `templated_email/welcome.md`:

   ```markdown
   {% block subject %}Welcome to Our Service{% endblock %}

   {% block preheader %}Thanks for signing up!{% endblock %}

   Hi {{ user.first_name }},

   Welcome to our service! We're glad to have you.

   **Enjoy your stay!**

   Best regards,
   The Team
   ```

3. **Send Templated Emails:**

   Use the `send_templated_mail` function to send emails:

   ```python
   from templated_email import send_templated_mail

   send_templated_mail(
       template_name='welcome',
       from_email='from@example.com',
       recipient_list=['to@example.com'],
       context={
           'user': user_instance,
           # Add other context variables if needed
       },
   )
   ```

   Ensure that you provide the necessary context variables used in your templates.

## Documentation

For more detailed information, please refer to the [full documentation][read the docs].

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_django-templated-email-md_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

We are grateful to the maintainers of the following projects
- [django-templated-email](https://github.com/vintasoftware/django-templated-email/)
- [emark](https://github.com/voiio/emark)


This project was generated from [@OmenApps]'s [Cookiecutter Django Package] template.

[@omenapps]: https://github.com/OmenApps
[pypi]: https://pypi.org/
[cookiecutter django package]: https://github.com/OmenApps/cookiecutter-django-package
[file an issue]: https://github.com/OmenApps/django-templated-email-md/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/OmenApps/django-templated-email-md/blob/main/LICENSE
[contributor guide]: https://github.com/OmenApps/django-templated-email-md/blob/main/CONTRIBUTING.md
[command-line reference]: https://django-templated-email-md.readthedocs.io/en/latest/usage.html
