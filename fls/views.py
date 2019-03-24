import numpy as np
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from fls.forms import CompetitionForm
from fls.lib import parse_formula, process_3_method, process_5_method
from fls.models import Param, Competition, Criterion, Group, ParamValue, CustomUser, WeightParamJury, Request, \
    CriterionValue, ParamResultWeight, RequestEstimation, EstimationJury, METHOD_CHOICES


@login_required(login_url="login/")
def criteria(request, id):
    comp = Competition.objects.get(id=id)
    params = Param.objects.filter(competition=comp)
    if request.method == "POST":
        c = Criterion(name=request.POST["name"], formula=request.POST["formula"], competition=comp)
        c.save()
        process_5_method(c)
        return redirect("fls:list_comp")
    return render(request, 'fls/add_criteria.html', {"params": params, "id": id})


@login_required(login_url="login/")
def comp(request):
    form = CompetitionForm()
    if request.method == 'POST':
        form = CompetitionForm(request.POST)
        if form.is_valid():
            comp = form.save()

            for text, desc, max in zip(request.POST.getlist('text'), request.POST.getlist('description'),
                                       request.POST.getlist('max')):
                Param.objects.create(name=text, description=desc, max=max, competition=comp)
            return redirect("fls:list_comp")

    return render(request, 'fls/add_comp.html', {"form": form})


@login_required(login_url="login/")
def list_comp(request):
    comps = Competition.objects.all()
    return render(request, 'fls/list_comp.html', {"comps": comps})


@login_required(login_url="login/")
def load_request(request, comp_id):
    participant = CustomUser.objects.get(user=request.user)
    if participant.role != 1:
        return HttpResponse("Данная страница для Вас недоступна")
    comp = Competition.objects.get(id=comp_id)
    params = Param.objects.filter(competition=comp)
    if request.method == 'POST':
        print(request.POST)
        req = Request(competition=comp, participant=participant)
        req.save()
        for p in params:
            pv = ParamValue(request=req, param=p, value=request.POST["value_%s" % p.id],
                            person_count=request.POST["person_%s" % p.id])
            pv.save()
        print("saving")
    return render(request, 'fls/load_request.html', {"params": params, "comp": comp})


@login_required(login_url="login/")
def pairwise_comparison(request, comp_id):
    jury = CustomUser.objects.get(user=request.user)
    if jury.role != 2:
        return HttpResponse("Данная страница для Вас недоступна")
    comp = Competition.objects.get(id=comp_id)
    params = Param.objects.filter(competition=comp)
    params_modif = {}
    for p in params:
        arr = []
        for f in params:
            arr.append("%s_%s" % (p.id, f.id))
        params_modif[p.name] = arr

    if request.method == 'POST':
        print(request.POST)
        values = dict(request.POST)
        del values['csrfmiddlewaretoken']
        param_rows = {}
        for key in values:
            param_id = key.split('_')[0].replace('rank', '')
            if not param_id in param_rows:
                param_rows[param_id] = [0.5]
            param_rows[param_id].append(float(values[key][0]))
        elems = sum(param_rows.values(), [])
        for key in param_rows:
            param = Param.objects.get(id=int(key))
            param_value = sum(param_rows[key]) / sum(elems)
            print(key, param_value, sep=' : ')
            if not WeightParamJury.objects.filter(type=3, param=param, jury=jury).exists():
                WeightParamJury.objects.create(type=3, param=param, jury=jury, value=param_value)
            else:
                w = WeightParamJury.objects.get(type=3, param=param, jury=jury)
                w.value = param_value
                w.save()
        process_3_method(jury, comp)
        return HttpResponse("Ваши оценки параметров сохранены")
    return render(request, 'fls/pairwise_comparison_table.html', {"params": params_modif, "comp": comp})


@login_required(login_url="login/")
def profile(request):
    user = CustomUser.objects.get(user=request.user)
    requests = Request.objects.filter(participant=user)
    new_requests = []
    view_requests = []
    select_comp = 0
    if request.method == "POST":
        comp_id = request.POST['comp']
        new_requests = Request.objects.filter(competition=Competition.objects.get(id=comp_id))
        for req in new_requests:
            result = EstimationJury.objects.filter(jury=user, request=req, type=1)
            if len(result) == 1:
                view_requests.append(req)
            new_requests = list(set(new_requests) - set(view_requests))
        select_comp = int(comp_id)
    print(select_comp)
    return render(request, "fls/profile.html",
                  {"cust_user": user, "requests": requests, 'comps': Competition.objects.all(),
                   'new_requests': new_requests, 'view_requests': view_requests, 'select_comp': select_comp})


def login_view(request):
    if not request.user.is_anonymous:
        return redirect("fls:profile")

    user = request.user
    if request.method == 'POST':
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is not None:
            login(request, user, backend=None)
            return redirect("fls:profile")
        else:
            error_message = 'User not found.' if not User.objects.filter(username=request.POST['username']).count() \
                else 'Password incorrect.'
            return render(request, 'fls/login.html', {'error': error_message,
                                                      'email': request.POST['username']})
    return render(request, 'fls/login.html', {})


def logout_page(request):
    logout(request)
    return redirect("fls:login_view")


def results(request):
    comps = Competition.objects.all()
    # method_choices = list(np.array(METHOD_CHOICES)[:, 1])[:-1]
    return render(request, 'fls/results.html', {'comps': comps})


def values(request):
    comp_id, type = int(request.GET['comp']), int(request.GET['type'])
    comp = Competition.objects.get(id=comp_id)
    estimations = EstimationJury.objects.filter(type=type, jury=request.user.custom_user,
                                                request__competition=comp).order_by('-value')
    estimation_values = {}
    params = comp.competition_params.all()
    for est in estimations:
        part_name = est.request.participant
        estimation_values[part_name] = [[], est.value]
        for param in params:
            param_value = ParamValue.objects.get(request=est.request, param=param).value
            estimation_values[part_name][0].append(param_value)
    data = {'est': render_to_string('fls/rank_table.html', {'ests': estimation_values, 'params': params})}
    return JsonResponse(data)


@login_required(login_url="login/")
def get_request(request, id):
    cur_request = Request.objects.get(id=id)
    estimate = EstimationJury.objects.filter(request=cur_request)
    flag = False
    dict = {'request': cur_request, 'user': CustomUser.objects.get(user=request.user)}
    if len(estimate) == 1:
        flag = True
        dict['estimate_id'] = estimate[0].id
        dict['estimate_val'] = estimate[0].value
    dict['estimate_flag'] = flag
    return render(request, 'fls/request.html', dict)


def estimate_req(request, req_id):
    if request.method == "POST":
        try:
            estimate = EstimationJury.objects.get(jury=CustomUser.objects.get(user=request.user),
                                                  request=Request.objects.get(id=req_id), type=1)
            estimate.value = request.POST["est_val"]

        except:
            estimate = EstimationJury(jury=CustomUser.objects.get(user=request.user),
                                      request=Request.objects.get(id=req_id),
                                      value=request.POST["est_val"], type=1)
        estimate.save()
    return redirect("fls:get_request", req_id)


def estimate_del(request, est_id):
    estimate = EstimationJury.objects.get(id=est_id)
    req_id = estimate.request.id
    estimate.delete()
    return redirect("fls:get_request", req_id)


def get_comp(request, id):
    comp = Competition.objects.get(id=id)
    user = CustomUser.objects.get(user=request.user)
    requests = Request.objects.filter(competition=Competition.objects.get(id=id))
    return render(request, 'fls/comp.html', {'comp': comp, 'user': user, 'requests': requests})


def common_results(request):
    comps = Competition.objects.all()
    jurys = CustomUser.objects.filter(role=2)
    # method_choices = list(np.array(METHOD_CHOICES)[:, 1])[:-1]
    return render(request, 'fls/common/results.html', {'comps': comps, 'jurys': jurys})


def common_values(request):
    comp_id, type = int(request.GET['comp']), request.GET['type']
    print(request.GET['type'])
    reqs = Request.objects.filter(competition_id=comp_id)
    params = Competition.objects.get(id=comp_id).competition_params.all()
    estimation_values = {}
    if type == 'all':
        methods = []
        for t in [1, 3, 5]:
            methods.append(METHOD_CHOICES[t - 1][1])
        for req in reqs:
            part_name = req.participant
            estimation_values[part_name] = [[], []]
            for param in params:
                param_value = ParamValue.objects.get(request=req, param=param).value
                estimation_values[part_name][0].append(param_value)
            for t in [1, 3]:
                estimation_values[part_name][1].append(
                    round(RequestEstimation.objects.get(type=t, request=req).value, 2))
                # hc
            criterion_value = Criterion.objects.filter(competition_id=comp_id).first().criterion_values.get(
                request=req).value
            estimation_values[part_name][1].append(round(criterion_value, 2))
        data = {'est': render_to_string('fls/common/table.html',
                                        {'ests': estimation_values, 'params': params, 'methods': methods})}
    else:
        jury = request.GET['jury']
        jurys = CustomUser.objects.filter(role=2) if jury == 'all' else [CustomUser.objects.get(
            id=int(jury))]
        one_method = True
        methods = []
        for req in reqs:
            part_name = req.participant
            estimation_values[part_name] = [[], []]
            for param in params:
                param_value = ParamValue.objects.get(request=req, param=param).value
                estimation_values[part_name][0].append(param_value)
            if type != '5':
                for jury in jurys:
                    estimation_values[part_name][1].append(
                        round(EstimationJury.objects.get(type=int(type), request=req, jury=jury).value, 2))
                estimation_values[part_name].append(
                    round(RequestEstimation.objects.get(type=int(type), request=req).value, 2))
                print(estimation_values)
            else:
                jurys = []
                one_method = False
                # methods.append(METHOD_CHOICES[int(type) - 1][1])
                # print(methods)
                criterion_value = Criterion.objects.filter(competition_id=comp_id).first().criterion_values.get(
                    request=req).value
                estimation_values[part_name][1].append(round(criterion_value, 2))
        if type == '5':
            methods.append(METHOD_CHOICES[int(type) - 1][1])
        data = {'est': render_to_string('fls/common/table.html',
                                        {'ests': estimation_values, 'params': params,
                                         'jurys': jurys, 'one_method': one_method, 'methods': methods})}
    return JsonResponse(data)
