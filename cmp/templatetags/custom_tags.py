from django.template.defaultfilters import register


@register.simple_tag()
def update_variable(value):
    data = value + 1
    return data


@register.filter(name='filter_equals')
def filter_equals(value):
    id1, id2 = value.split("_")
    return id1 == id2
