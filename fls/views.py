import traceback
import math
from operator import itemgetter

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from fls.forms import CompetitionForm
from fls.lib import parse_formula, process_3_method, process_5_method, process_request, union_request_ests, make_ranks, \
    dist_kemeni, clusterization
from fls.models import Param, Competition, Criterion, Group, ParamValue, CustomUser, WeightParamJury, Request, \
    CriterionValue, ParamResultWeight, RequestEstimation, EstimationJury, METHOD_CHOICES, TYPE_SUBPARAM, SubParam, \
    STATUSES, SubParamValue, UploadData

STATUS = ["SubParam", "Criteria", "SingleParam"]


@login_required(login_url="login/")
def criteria(request, id):
    comp = Competition.objects.get(id=id)
    subparams = []
    params = Param.objects.filter(competition=comp)
    for p in params:
        [subparams.append(sb) for sb in p.subparam_params.all().filter(for_formula=True)]
    if request.method == "POST":
        c = Criterion(competition=comp, name=request.POST["name"], formula=request.POST["formula"])
        c.save()
        return redirect("fls:list_comp")
    return render(request, 'fls/add_criteria.html', {"subparams": subparams, "id": id})


@login_required(login_url="login/")
def result_criteria(request, id):
    comp = Competition.objects.get(id=id)
    criteria = Criterion.objects.filter(competition=comp, result_formula=False)
    if request.method == "POST":
        c = Criterion(competition=comp, name=request.POST["name"], formula=request.POST["formula"], result_formula=True)
        c.save()
        return redirect("fls:list_comp")
    return render(request, 'fls/add_result_criteria.html', {"criteria": criteria, "id": id})


@login_required(login_url="login/")
def criteria_for_single_param(request, id, param_id):
    comp = Competition.objects.get(id=id)
    param = Param.objects.get(id=param_id)
    subparams = param.subparam_params.all().filter(for_formula=True)
    len_1 = len(comp.competition_criterions.all().filter(param__isnull=False))
    len_2 = len(comp.competition_params.all())
    print(len_1, len_2)
    next = True
    if request.method == "POST":
        c = Criterion(competition=comp, name=request.POST["name"], formula=request.POST["formula"], result_formula=True,
                      param=param)
        c.save()
        len_1 += 1
        if len_1 == len_2:
            return redirect("fls:list_comp")
    if (len_2 - len_1) == 1:
        next = False
    return render(request, 'fls/add_criteria_for_single_param.html',
                  {"subparams": subparams, "id": id, "p": Param.objects.get(id=comp.get_param_for_criteria()),
                   "next": next})


@login_required(login_url="login/")
def calculate_result(request, id):
    user = CustomUser.objects.get(user=request.user)
    comp = Competition.objects.get(id=id)
    if user.is_organizer():
        if comp.method_of_estimate == 1:
            # проходимся по всем заявкам, и берем среднее по результатам жюри, затем проставление данных оценок в заявку
            pass
        elif comp.method_of_estimate == 4:
            # для всех params заявки высчитываем соответсвующую формулу и умножаем на вес (параметра)  и складываем результат пишем в заявку
            pass
        elif comp.method_of_estimate == 5:
            # для каждой формулы критерия подсчитываем на основе subpapramsvalue и сохраняем, после по итоговой формуле подставляем значения критериев, результат пишем в заявку
            pass
    return redirect("fls:get_comp", id)


@login_required(login_url="login/")
def comp(request):
    form = CompetitionForm()
    if request.method == 'POST':
        key = "params[%s][%s]"
        print(request.POST)
        form = CompetitionForm(request.POST)
        if form.is_valid():
            print("create comp")
            comp = form.save()
        else:
            return render(request, 'fls/add_comp.html', {"form": form, "types": TYPE_SUBPARAM})
        i = 0
        while True:
            try:
                name = request.POST[key % (i, "name")]
                desc = request.POST[key % (i, "description")]
                p = Param(competition=comp, name=name, description=desc)
                p.save()
                print(name)
                k = 0
                while True:
                    try:
                        name_sub = request.POST["%s[%s][%s]" % ((key % (i, "subparams")), k, "name")]
                        type = int(request.POST["%s[%s][%s]" % ((key % (i, "subparams")), k, "type_subparam")])
                        print(type)
                        flag = False if "false" == request.POST[
                            "%s[%s][%s]" % ((key % (i, "subparams")), k, "for_formula")] else True
                        print(flag)
                        sub_p = SubParam(param=p, name=name_sub, type=type, for_formula=flag)
                        sub_p.save()
                        print(name_sub)
                        k += 1
                    except Exception as e:
                        print(e)
                        break
                i += 1
            except Exception as e:
                print(e)
                break

    return render(request, 'fls/add_comp.html', {"form": form, "types": TYPE_SUBPARAM})


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
    collection = []
    for p in params:
        subparams = SubParam.objects.filter(param=p)
        collection.append({"param": p, "subparams": subparams})
    if request.method == 'POST':
        print(request.POST)
        req = Request(competition=comp, participant=participant)
        req.save()
        for c in collection:
            for subparam in c["subparams"]:
                sp_val = SubParamValue(subparam=subparam, request=req)
                sp_val.save()
                if subparam.type == 3 or subparam.type == 4:
                    print(request.FILES)
                    for image, h in zip(request.FILES.getlist("file_%s" % subparam.id), request.POST.getlist(
                            "header_%s" % subparam.id)):
                        print(image)
                        link_file = "%s/%s/%s" % (participant.id, comp_id, image)
                        fs = FileSystemStorage()
                        filename = fs.save(link_file, image)
                        u = UploadData(header_for_file=h, image=filename, sub_param_value=sp_val)
                        u.save()
                else:
                    val = request.POST["sp_%s" % subparam.id]
                    if subparam.type == 1:
                        sp_val.value = val
                    elif subparam.type == 2 or subparam.type == 6:
                        sp_val.text = val
                    else:
                        sp_val.enum_val = val
                    sp_val.save()
        # не знаю как сейчас это применяется

        # до этого все жюри должны были выставить свои кф и эксперты должны были задать свои формулы
        # объединение по абсолютным оценкам происходит в estimate_req со своими условиями

        # process_request(req.id, union_types=(3,))
        print("saving")
        return redirect("fls:profile")

    return render(request, 'fls/load_request.html', {"comp": comp, "collection": collection})


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
    return render(request, "fls/profile.html",
                  {"cust_user": user, "requests": requests, 'comps': Competition.objects.all(),
                   'new_requests': new_requests, 'view_requests': view_requests, 'select_comp': select_comp,
                   'statuses': STATUSES})


def ajax_comp_status(request):
    status = request.GET["status"]
    comps = Competition.objects.filter(status=status)
    return JsonResponse(
        {'est': render_to_string('fls/part_organizer_profile.html', {"org_comps": comps, "statuses": STATUSES,
                                                                     "selected_status": int(status)})})


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
    arr = []
    params = Param.objects.filter(competition=cur_request.competition)
    for p in params:
        subvalues = []
        for sb in p.subparam_params.all():
            sbvalue = SubParamValue.objects.get(subparam=sb, request=cur_request)
            subvalues.append(sbvalue)
        arr.append((p, subvalues))
    dict = {'request': cur_request, 'values': arr, 'user': CustomUser.objects.get(user=request.user)}
    if len(estimate) == 1:
        flag = True
        dict['estimate_id'] = estimate[0].id
        dict['estimate_val'] = estimate[0].value
    dict['estimate_flag'] = flag
    return render(request, 'fls/request.html', dict)


def estimate_req(request, req_id):
    req = Request.objects.get(id=req_id)
    if request.method == "POST":
        try:
            estimate = EstimationJury.objects.get(jury=CustomUser.objects.get(user=request.user),
                                                  request=req, type=1)
            estimate.value = request.POST["est_val"]

        except:
            estimate = EstimationJury(jury=CustomUser.objects.get(user=request.user),
                                      request=req,
                                      value=request.POST["est_val"], type=1)
        estimate.save()
        jurys_count = CustomUser.objects.filter(role=2).count()
        request_estimations_count = EstimationJury.objects.filter(request=req,
                                                                  type=1).count()
        if request_estimations_count == jurys_count:

            for jury_formula in req.competition.competition_formula_for_jury.all():
                union_request_ests(req, jury_formula, types=(1,))

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
            estimation_values[part_name] = ([], [])
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


def similar_page(request):
    comps = Competition.objects.all()
    jurys = CustomUser.objects.filter(role=2)
    return render(request, 'fls/sim_jury/sim_jury.html', {'comps': comps, 'jurys': jurys})


def similar_jury(request):
    comp_id, type, jury_id = int(request.GET['comp']), int(request.GET['type']), int(request.GET['jury'])
    reqs = Request.objects.filter(competition_id=comp_id)
    params = Competition.objects.get(id=comp_id).competition_params.all()
    slt_jury = CustomUser.objects.get(id=jury_id)
    slt_ests = make_ranks([EstimationJury.objects.get(jury=slt_jury, type=type, request=req).value for req in reqs])
    rest_jury = CustomUser.objects.filter(role=2).exclude(id=jury_id)
    smt = {}
    jury_ests = {}
    for jury in rest_jury:
        s = 0
        jury_ests[jury.id] = []
        for req in reqs:
            slt_value = EstimationJury.objects.get(jury=slt_jury, type=type, request=req).value
            jury_value = EstimationJury.objects.get(jury=jury, type=type, request=req).value
            jury_ests[jury.id].append(jury_value)
            s += abs(slt_value - jury_value)
        jury_ests[jury.id] = make_ranks(jury_ests[jury.id])
        smt[jury.id] = round(s, 2)
    print('smt', smt)
    if request.GET['key'] == 'est':

        sorted_smt = dict(sorted(smt.items(), key=lambda item: item[1]))
    else:
        sorted_kemeni = {key: dist_kemeni(slt_ests, jury_ests[key]) for key in smt}
        sorted_smt = dict(sorted(sorted_kemeni.items(), key=lambda item: item[1]))

    print('sorted_smt', sorted_smt)
    clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(list(sorted_smt.keys()))])
    ordering = 'CASE %s END' % clauses
    sorted_jury = CustomUser.objects.filter(pk__in=list(sorted_smt.keys())).extra(
        select={'ordering': ordering}, order_by=('ordering',))
    print(sorted_jury)
    estimation_values = {}
    for i, req in enumerate(reqs):
        part_name = req.participant
        estimation_values[part_name] = ([], [])
        estimation_values[part_name][0].extend(
            ParamValue.objects.get(request=req, param=param).value for param in params)
        estimation_values[part_name][1].append((
            round(EstimationJury.objects.get(type=type, jury=slt_jury, request=req).value, 2), slt_ests[i]))
        estimation_values[part_name][1].extend(
            [(round(EstimationJury.objects.get(type=type, jury=jury, request=req).value, 2), jury_ests[jury.id][i]) for
             jury in sorted_jury])
    diff = sorted_smt.values()
    est_key = request.GET['key'] == 'est'
    data = {'est': render_to_string('fls/sim_jury/table.html',
                                    {'ests': estimation_values, 'jurys': sorted_jury, 'params': params,
                                     'slt_jury': slt_jury, 'diffs': diff, 'est_key': est_key})}
    return JsonResponse(data)


def metcomp_page(request):
    comps = Competition.objects.all()
    jurys = CustomUser.objects.filter(role=2)
    return render(request, 'fls/metcomp/metcomp.html', {'comps': comps, 'jurys': jurys})


def metcomp(request):
    method_indexes = (0, 2)
    methods = itemgetter(*method_indexes)(METHOD_CHOICES)
    comp_id, jury_id = int(request.GET['comp']), int(request.GET['jury'])
    reqs = Request.objects.filter(competition_id=comp_id)
    params = Competition.objects.get(id=comp_id).competition_params.all()
    slt_jury = CustomUser.objects.get(id=jury_id)
    estimation_values = {}
    for req in reqs:
        part_name = req.participant
        estimation_values[part_name] = [[], []]
        estimation_values[part_name][0].extend(
            ParamValue.objects.get(request=req, param=param).value for param in params)
        estimation_values[part_name][1].extend(
            round(EstimationJury.objects.get(request=req, jury=slt_jury, type=tp[0]).value, 2) for tp in methods)
        diff = round((estimation_values[part_name][1][0] - estimation_values[part_name][1][1]), 2)
        estimation_values[part_name].append(diff)
    data = {'est': render_to_string('fls/metcomp/table.html',
                                    {'ests': estimation_values, 'params': params,
                                     'slt_jury': slt_jury, 'methods': methods})}

    return JsonResponse(data)


def dev_page(request):
    comps = Competition.objects.all()
    return render(request, 'fls/dev/dev.html', {'comps': comps})


def deviation(request):
    comp_id, type, req_id = int(request.GET['comp']), int(request.GET['type']), int(request.GET['reqs'])
    params = Competition.objects.get(id=comp_id).competition_params.all()
    req = Request.objects.get(id=req_id)
    params_values = {param.name: ParamValue.objects.get(request=req, param=param).value for param in params}
    common_value = round(RequestEstimation.objects.get(request=req, type=type).value, 2)
    jury_est_values = {}
    jurys = CustomUser.objects.filter(role=2)
    for jury in jurys:
        jury_est_values[jury] = []
        jury_est = EstimationJury.objects.get(jury=jury, type=type, request=req).value
        jury_est_values[jury].extend([round(jury_est, 2), round((jury_est - common_value), 2)])
    jury_est_values = sorted(jury_est_values.items(), key=lambda item: item[1][1], reverse=True)
    avg_dev = round(sum([abs(elem[1][1]) for elem in jury_est_values]) / len(jury_est_values), 2)
    print(jury_est_values)
    print(params_values)
    variation_coef = math.sqrt(
        sum([dev[1][1] ** 2 for dev in jury_est_values]) / (len(jury_est_values) - 1)) / common_value
    data = {'est': render_to_string('fls/dev/table.html',
                                    {'ests': jury_est_values, 'param_values': params_values, 'comm': common_value,
                                     'avg_dev': avg_dev, 'var_coef': round(variation_coef, 2)})}
    return JsonResponse(data)


def comp_reqs(request):
    reqs = Competition.objects.get(id=request.GET['comp']).competition_request.all()
    data = {'reqs': render_to_string('fls/dev/reqs.html', {'reqs': reqs})}
    return JsonResponse(data)


def change_status(request, id, val):
    comp = Competition.objects.get(id=id)
    comp.status = int(val)
    comp.save()
    return redirect("fls:get_comp", id)


def coherence_page(request):
    comps = Competition.objects.all()
    jury_count = list(range(1, CustomUser.objects.filter(role=2).count()))
    return render(request, 'fls/coher/coher.html', {'comps': comps, 'jury_count': jury_count})


def coherence(request):
    comp_id, type, clusts = int(request.GET['comp']), int(request.GET['type']), int(request.GET['clusts'])
    reqs = Competition.objects.get(id=comp_id).competition_request.all()
    jurys = CustomUser.objects.filter(role=2)
    jury_ranks = {}
    for jury in jurys:
        jury_ranks[jury] = make_ranks(
            [EstimationJury.objects.get(type=type, jury=jury, request=req).value for req in reqs], method='average',
            s_m=True)
    req_values = {}
    for idx, req in enumerate(reqs):
        req_values[req] = sum([jury_ranks[jury][0][idx] for jury in jurys])
    try:
        common_rank_req_sum_avg = sum(list(req_values.values())) / len(reqs)
        dev_sum = 0
        for req in req_values:
            dev_sum += (req_values[req] - common_rank_req_sum_avg) ** 2
        sum_T = 0
        for jury in jury_ranks:
            sum_T += sum([el ** 3 - el for el in jury_ranks[jury][1]])
        kendall_coef = round((12 * dev_sum / ((len(jurys) ** 2) * (len(reqs) ** 3 - len(reqs)) - len(jurys) * sum_T)),
                             2)
    except:
        kendall_coef = None

    jury_rankings = [make_ranks(
        [EstimationJury.objects.get(type=type, jury=jury, request=req).value for req in reqs], method='min') for
        jury in jurys]
    labels, centroids = clusterization(jury_rankings, clusts)
    clusters_jury = {}
    clusters = {}
    for label in set(labels):
        clusters[label] = []
        clusters_jury[label] = []
        clusters[label].append(centroids[label])
    for idx, label in enumerate(labels):
        clusters[label].append(jury_rankings[idx])
        clusters_jury[label].append(jurys[idx])
    req_ranks = {}
    for idx, req in enumerate(reqs):
        req_ranks[req.participant] = []
        for label in clusters:
            label_values = []
            for ranking in clusters[label]:
                label_values.append(ranking[idx])
            req_ranks[req.participant].append(label_values)
    data = {'est': render_to_string('fls/coher/table.html',
                                    {'req_ranks': req_ranks, 'kendall_coef': kendall_coef,
                                     'clusters_jury': clusters_jury})}

    return JsonResponse(data)
