"""Test cases for the django-templated-email-md package."""

from django.apps import apps
from django.conf import settings


def test_succeeds() -> None:
    """Test that the test suite runs."""
    assert 0 == 0


def test_settings() -> None:
    """Test that the settings are configured."""
    assert settings.USE_TZ is True


def test_apps() -> None:
    """Test that the app is configured in the Django project."""
    assert "templated_email_md" in apps.get_app_config("templated_email_md").name
