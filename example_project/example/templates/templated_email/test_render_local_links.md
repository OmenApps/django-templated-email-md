{% block content %}

# Hello {{ name }}!

This is a test message with a link to [index]({% url "index" some_id=some_id %}) using the template tag.

This is a test message with a link to [index]({{ url }}) using the context variable.

Both should render the same link.
{% endblock %}
