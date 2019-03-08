from django.conf.urls import url

from fls.views import *

app_name = "fls"

urlpatterns = [
    url(r'^criteria/(?P<id>\d+)/$', criteria, name="criteria"),
    url(r'^comps', list_comp, name="list_comp"),
    url(r'^comp$', comp, name="comp"),
]
