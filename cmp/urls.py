from django.conf.urls import url

from cmp.views import *

app_name = "cmp"

urlpatterns = [

    url(r'^groups$', cmp_estimations, name="groups"),
    url(r'^calc$', calculate_estimations_difference, name="calc"),
]
