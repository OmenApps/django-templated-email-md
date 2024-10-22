{% load i18n %}{% block subject %}{% trans "Welcome to Our Service" %}{% endblock %}

{% block preheader %}{% trans "Thanks for signing up!" %}{% endblock %}

{% block content %}

# {% trans "Welcome" %}, {{ user.first_name }}!

{% trans "We're thrilled to have you join our service. Here are a few things you can do to get started:" %}

1. **{% trans "Complete your profile" %}**
2. **{% trans "Explore our features" %}**
3. **{% trans "Connect with other users" %}**

{% trans "If you have any questions, don't hesitate to reach out to our support team." %}

{% trans "Best regards," %}
{% trans "The Team" %}
{% endblock %}
