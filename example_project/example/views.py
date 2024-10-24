"""Views for the example app."""

from django.template.response import TemplateResponse


def index(request, some_id):
    """Render the index page."""
    template = "example/index.html"

    context = {
        "message": "Hello, world!",
        "some_id": some_id,
    }
    return TemplateResponse(request, template, context)
