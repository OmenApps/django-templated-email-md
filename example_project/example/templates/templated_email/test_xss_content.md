{% block subject %}XSS Test Email{% endblock %}

{% block preheader %}XSS test{% endblock %}

{% block content %}
# XSS Test

Normal paragraph text.

<script>alert('xss')</script>

More safe content here.
{% endblock %}
