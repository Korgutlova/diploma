from django.template.defaultfilters import register


@register.simple_tag()
def update_variable(value):
    data = value + 1
    return data
