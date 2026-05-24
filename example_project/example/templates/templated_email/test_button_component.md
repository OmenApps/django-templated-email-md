{% block subject %}Button Component Test{% endblock %}

{% block content %}
# Test Button

Click the button below to continue.

{% include "templated_email/components/button.html" with url="https://example.com/go" label="Click Me" %}

Thank you.
{% endblock %}
