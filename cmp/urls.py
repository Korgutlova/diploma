from django.conf.urls import url

from cmp.views import *

app_name = "cmp"

urlpatterns = [
    url(r'^base$', base_page, name="base"),
    url(r'^best$', best_weights, name="best"),
    url(r'^load/(?P<id>[0-9]+)$', load_data, name="load_db"),
]
