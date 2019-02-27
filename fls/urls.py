from django.conf.urls import url

from fls.views import *

app_name = "fls"

urlpatterns = [
    url(r'^params$', params, name="params"),
]
