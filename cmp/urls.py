from django.conf.urls import url

from cmp.views import *

app_name = "cmp"

urlpatterns = [

    url(r'^main$', cmp_estimations, name="main"),
    url(r'^calc$', calculate_estimations_difference, name="calc"),
]
