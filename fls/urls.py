from django.conf.urls import url
from fls.views import *

app_name = "fls"

urlpatterns = [
    url(r'^$', login_view),
    url(r'^logout$', logout_page, name='logout'),
    url(r'^profile$', profile, name="profile"),
    url(r'^login/$', login_view, name="login_view"),
    url(r'^criteria/(?P<id>\d+)/$', criteria, name="criteria"),
    url(r'^comps$', list_comp, name="list_comp"),
    url(r'^comp$', comp, name="comp"),
    url(r'^comp/(?P<id>\d+)$', get_comp, name="get_comp"),
    url(r'^load_request/(?P<comp_id>\d+)/$', load_request, name="load_request"),
    url(r'^comp/(?P<comp_id>\d+)/pairwise_comparison$', pairwise_comparison, name="pairwise_comparison"),
    url(r'^preq/(?P<id>\d+)/$', process_request, name="preq"),
    url(r'^results/$', results, name="results"),
    url(r'^jury_values/$', values, name="values"),
    url(r'^request/(?P<id>\d+)/$', get_request, name="get_request"),
    url(r'^estimate_req/(?P<req_id>\d+)/$', estimate_req, name="estimate_req"),
    url(r'^estimate_del/(?P<est_id>\d+)/$', estimate_del, name="estimate_del"),
    url(r'^commres/$', common_results, name="common"),
    url(r'^common_values/$', common_values, name="common_values"),
]
