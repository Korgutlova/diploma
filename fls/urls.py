from django.conf.urls import url
from fls.views import *

app_name = "fls"

urlpatterns = [
    url(r'^$', login_view),
    url(r'^logout$', logout_page, name='logout'),
    url(r'^profile$', profile, name="profile"),
    url(r'^login/$', login_view, name="login_view"),
    url(r'^criteria/(?P<id>\d+)/$', criteria, name="criteria"),
    url(r'^criteria/(?P<id>\d+)/result$', result_criteria, name="result_criteria"),
    url(r'^criteria/(?P<id>\d+)/single_param/(?P<param_id>\d+)$', criteria_for_single_param,
        name="criteria_for_single_param"),
    url(r'^comps$', list_comp, name="list_comp"),
    url(r'^comp$', comp, name="comp"),
    url(r'^comp/(?P<id>\d+)$', get_comp, name="get_comp"),
    url(r'^load_request/(?P<comp_id>\d+)/$', load_request, name="load_request"),
    url(r'^comp/(?P<comp_id>\d+)/pairwise_comparison$', pairwise_comparison,
        name="pairwise_comparison"),
    url(r'^crit/(?P<crit_id>\d+)/pairwise_comparison$', pairwise_comparison_param,
        name="pairwise_comparison_param"),
    url(r'^request/(?P<id>\d+)/$', get_request, name="get_request"),
    url(r'^estimate_req/(?P<req_id>\d+)/$', estimate_req, name="estimate_req"),
    url(r'^estimate_del/(?P<est_id>\d+)/$', estimate_del, name="estimate_del"),
    url(r'^simjury/$', similar_page, name="simjury"),
    url(r'^similar_jury/$', similar_jury, name="similar_jury"),
    url(r'^ajax_comp_status/$', ajax_comp_status, name="ajax_comp_status"),
    url(r'^metcomp/$', metcomp_page, name="metcomp"),
    url(r'^method_comp/$', metcomp, name="method_comp"),
    url(r'^dev/$', dev_page, name="devpage"),
    url(r'^deviation/$', deviation, name="dev"),
    url(r'^comp_reqs/$', comp_reqs, name="compreqs"),
    url(r'^comp/(?P<id>\d+)/change_status/(?P<val>\d+)$', change_status, name="change_status"),
    url(r'^coherence/$', coherence_page, name="coherpage"),
    url(r'^coher/$', coherence, name="coher"),
    url(r'^comp/(?P<id>\d+)/calculate_result$', calculate_result, name="calculate_result"),
]
