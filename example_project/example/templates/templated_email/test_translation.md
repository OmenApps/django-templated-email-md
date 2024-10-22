{% load i18n %}

{% block subject %}{% trans "Test Email" %}{% endblock %}

{% block content %}

# {% trans "Hello" %} {{ name }}!

{% trans "This is a test email." %}
{% endblock %}
