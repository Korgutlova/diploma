from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect

from fls.forms import CompetitionForm
from fls.lib import parse_formula
from fls.models import Param, Competition, Criterion, Group, ParamValue, CustomUser, WeightParamJury, Request, \
    CriterionValue, ParamResultWeight, RequestEstimation, EstimationJury


@login_required(login_url="login/")
def criteria(request, id):
    comp = Competition.objects.get(id=id)
    params = Param.objects.filter(competition=comp)
    if request.method == "POST":
        c = Criterion(name=request.POST["name"], formula=request.POST["formula"], competition=comp)
        c.save()
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


def process_request(request, id):
    req = Request.objects.get(id=id)
    params = req.competition.competition_params.all()
    param_values = []
    pair_result = 0
    rank_result = 0
    for param in params:
        param_value = ParamValue.objects.get(param=param, request=req).value
        pair_result += ParamResultWeight.objects.get(param=param, type=3).weight_value * param_value
        rank_result += ParamResultWeight.objects.get(param=param, type=4).weight_value * param_value
        param_values.append(param_value)
    RequestEstimation.objects.create(type=3, request=req, value=pair_result)
    RequestEstimation.objects.create(type=4, request=req, value=rank_result)
    for criterion in req.competition.competition_criterions.all():
        value = parse_formula(criterion.formula, param_values)
        print('value', value)
        CriterionValue.objects.create(criterion=criterion, request=req, value=value)
    jurys = CustomUser.objects.filter(role=2)
    for jury_formula in req.competition.competition_formula_for_jury.all():
        request_abs_values = []
        request_pair_values = []
        for jury in jurys:
            request_abs_values.append(EstimationJury.objects.get(type=1, jury=jury, request=req).value)
            request_pair_values.append(EstimationJury.objects.get(type=2, jury=jury, request=req).value)
        abs_value = parse_formula(jury_formula.formula, request_abs_values)
        pair_value = parse_formula(jury_formula.formula, request_pair_values)
        RequestEstimation.objects.create(type=1, request=req, value=abs_value, jury_formula=jury_formula)
        RequestEstimation.objects.create(type=2, request=req, value=pair_value, jury_formula=jury_formula)
    return HttpResponse('OK')


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
                WeightParamJury.objects.create(type=3, param=param, jury=jury)
            else:
                w = WeightParamJury.objects.get(type=3, param=param, jury=jury)
                w.value = param_value
                w.save()
        return HttpResponse("Ваши оценки параметров сохранены")
    return render(request, 'fls/pairwise_comparison_table.html', {"params": params_modif, "comp_id": comp_id})


@login_required(login_url="login/")
def profile(request):
    return render(request, "fls/profile.html", {"cust_user": CustomUser.objects.get(user=request.user)})


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
