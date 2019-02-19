from django.conf.urls import url

from cmp.views import *

app_name = "cmp"

urlpatterns = [
    url(r'^base$', base_page, name="base"),
    url(r'^base$', calculate, name="calculate"),
]
