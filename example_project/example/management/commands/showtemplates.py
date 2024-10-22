"""A management command to list all templates in the project."""
import os
from importlib import import_module

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import get_template


class Command(BaseCommand):
    """A management command to list all templates in the project."""
    help = "List all templates"

    def handle(self, *args, **options):
        templates = []
        for app in settings.INSTALLED_APPS:
            try:
                app_module = import_module(app)
                app_dir = os.path.dirname(app_module.__file__)
                templates_dir = os.path.join(app_dir, 'templates')

                if os.path.exists(templates_dir):
                    for root, _, files in os.walk(templates_dir):
                        for file in files:
                            templated_email_file_extension = getattr(settings, 'TEMPLATED_EMAIL_FILE_EXTENSION', 'md')
                            if file.endswith('.html') or file.endswith(f'.{templated_email_file_extension}'):
                                template_path = os.path.join(root, file)
                                try:
                                    get_template(template_path)
                                    templates.append(template_path)
                                except Exception:
                                    pass
            except ImportError:
                pass

        self.stdout.write('\n'.join(templates))
