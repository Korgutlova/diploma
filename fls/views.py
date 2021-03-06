import os
import statistics
import time

import numpy as np

import cexprtk
import math
from operator import itemgetter

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from dipl.settings import BASE_DIR
from fls.forms import CompetitionForm
from fls.lib import make_ranks, dist_kemeni, clusterization, calculate_jury_automate_ests, \
    define_optimal_k, max_dist_kemeni_for_ranking
from fls.models import Competition, Criterion, CustomUser, Request, \
    CriterionValue, EstimationJury, METHOD_CHOICES, TYPE_PARAM, Param, \
    STATUSES, ParamValue, UploadData, WeightParamJury, CustomEnum, ValuesForEnum, ClusterNumber, Invitation
from py_expression_eval import Parser

parser = Parser()

DICT_FUNCTIONS = ["max", "min", "summa", "average", "median", "mode"]


@login_required(login_url="login/")
def result_criteria(request, id):
    comp = Competition.objects.get(id=id)
    criteria = Criterion.objects.filter(competition=comp, result_formula=False)
    if request.method == "POST":
        cr = Criterion.objects.filter(competition=comp, result_formula=True)
        c = cr[0]
        c.formula = request.POST["formula"]
        c.save()
        return redirect("fls:list_comp")
    return render(request, 'fls/add_result_formula.html', {"criteria": criteria, "id": id, "funcs": DICT_FUNCTIONS})


@login_required(login_url="login/")
def formula_for_single_criteria(request, id, cr_id):
    comp = Competition.objects.get(id=id)
    criteria = Criterion.objects.get(id=cr_id)
    params = criteria.param_criterion.all().filter(for_formula=True)
    len_1 = len(comp.competition_criterions.all().exclude(formula=None).filter(result_formula=False))
    len_2 = len(comp.competition_criterions.all().filter(result_formula=False))
    print(len_1, len_2)
    print(params)
    print(cr_id)
    next = True
    if request.method == "POST":
        criteria.formula = request.POST["formula"]
        criteria.save()
        len_1 += 1
        if len_1 == len_2:
            return redirect("fls:list_comp")
        else:
            criteria = Criterion.objects.get(id=comp.get_next_criterion())
            params = criteria.param_criterion.all().filter(for_formula=True)

    if (len_2 - len_1) == 1:
        next = False
    return render(request, 'fls/add_formula.html',
                  {"params": params, "id": id, "c": criteria, "next": next, "funcs": DICT_FUNCTIONS})


def average(*args):
    return np.average(args)


def median(*args):
    return statistics.median(*args)


def summa(*args):
    return np.sum(args)


def mode(*args):
    return statistics.mode(*args)


def calculate_avg_request(comp):
    requests = comp.competition_request.all()
    final_criteria = comp.competition_criterions.get(result_formula=True)
    for r in requests:
        estimations = EstimationJury.objects.filter(request=r, criterion=final_criteria, type=1).values_list("value",
                                                                                                             flat=True)
        result = average(estimations)
        r.result_value = result
        r.save()
    print("done")


def calculate_result_for_ranking(comp):
    requests = comp.competition_request.all()
    criteria = comp.competition_criterions.all().filter(result_formula=False)
    for r in requests:
        sum = 0
        for c in criteria:
            vars, funcs = get_vars_and_funcs(c.formula)
            array = {}
            for v in vars:
                id = int(v[2:])
                print(id)
                param = Param.objects.get(id=id)
                print(param)
                spv = ParamValue.objects.get(param=param, request=r)
                print(spv)
                if param.type == 1:
                    array[v] = spv.value
                elif param.type == 5:
                    array[v] = spv.enum_val.enum_value
                elif param.type == 3 or param.type == 4:
                    array[v] = spv.files.all().count()
                else:
                    print("Неверный формат")
            result = execute_formula(array, funcs, c.formula) * c.weight_value
            cv = CriterionValue.objects.filter(criterion=c, request=r)
            if cv.exists():
                cv[0].value = result
                cv[0].save()
            else:
                cv = CriterionValue(criterion=c, request=r, value=result)
                cv.save()
            sum += result
            print("result %s" % result)
        r.result_value = sum
        r.save()
    print("done")


def get_vars_and_funcs(formula):
    print(formula)
    vars_func = parser.parse(formula).variables()
    print(vars_func)
    vars = list(filter(lambda x: x.find('_') != -1, vars_func))
    print(vars)
    funcs = list(filter(lambda x: x.find('_') == -1, vars_func))
    print(funcs)
    return vars, funcs


def execute_formula(array, funcs, formula):
    st = cexprtk.Symbol_Table(array)
    for func in funcs:
        st.functions[func] = globals()[func]
    calc_exp = cexprtk.Expression(formula, st)
    return calc_exp()


def calculate_result_criteria(comp):
    requests = comp.competition_request.all()
    criteria = comp.competition_criterions.all().filter(result_formula=False)
    result_criteria = comp.competition_criterions.all().get(result_formula=True)
    for c in criteria:
        vars, funcs = get_vars_and_funcs(c.formula)
        for r in requests:
            array = {}
            for v in vars:
                id = int(v[2:])
                print(id)
                param = Param.objects.get(id=id)
                print(param)
                spv = ParamValue.objects.get(param=param, request=r)
                print(spv)
                if param.type == 1:
                    array[v] = spv.value
                elif param.type == 5:
                    array[v] = spv.enum_val.enum_value
                elif param.type == 3 or param.type == 4:
                    array[v] = spv.files.all().count()
                else:
                    print("Неверный формат")
            result = execute_formula(array, funcs, c.formula)
            cv = CriterionValue.objects.filter(criterion=c, request=r)
            if cv.exists():
                cv[0].value = result
                cv[0].save()
            else:
                cv = CriterionValue(criterion=c, request=r, value=result)
                cv.save()
            print("result %s" % result)

    print("result criteria %s " % result_criteria.formula)
    vars, funcs = get_vars_and_funcs(result_criteria.formula)
    for r in requests:
        array = {}
        for v in vars:
            id = int(v[2:])
            print(id)
            criterion = Criterion.objects.get(id=id)
            print(criterion)
            cv = CriterionValue.objects.get(request=r, criterion=criterion)
            array[v] = cv.value
        result = execute_formula(array, funcs, result_criteria.formula)
        r.result_value = result
        r.save()
    print("done")


@login_required(login_url="login/")
def calculate_result(request, id):
    user = CustomUser.objects.get(user=request.user)
    comp = Competition.objects.get(id=id)
    if user.is_organizer():
        if comp.method_of_estimate == 1:
            calculate_avg_request(comp)
        elif comp.method_of_estimate == 2:
            calculate_result_for_ranking(comp)
        elif comp.method_of_estimate == 3:
            calculate_result_criteria(comp)
    return redirect("fls:get_result", comp.id)


@login_required(login_url="login/")
def get_result(request, id):
    comp = Competition.objects.get(id=id)
    requests = comp.competition_request.all().extra(
        select={'result': 'CAST(result_value AS INTEGER)'}
    ).order_by("-result")
    return render(request, "fls/result_competition.html", {"comp": comp, "requests": requests})


@login_required(login_url="login/")
def comp_first_step(request):
    form = CompetitionForm()
    print(1)
    if request.method == 'POST':
        key = "params[%s][%s]"
        print(request.POST)
        request.POST = request.POST.copy()
        form = CompetitionForm(request.POST)
        if form.is_valid():
            print("create comp")
            comp = form.save()
            if comp.method_of_estimate == 1:
                for j_id in request.POST.getlist("jurys[]"):
                    invitation = Invitation(competition=comp, jury=CustomUser.objects.get(id=int(j_id)))
                    invitation.save()
            comp.organizer = CustomUser.objects.get(user=request.user)
            comp.save()
        else:
            return render(request, 'fls/add_comp_first.html', {"form": form})
        i = 0
        while True:
            try:
                name = request.POST[key % (i, "name")]
                en = CustomEnum(competition=comp, name=name)
                en.save()
                print(name)
                k = 0
                while True:
                    try:
                        text_enum = request.POST["%s[%s][%s]" % ((key % (i, "subparams")), k, "text")]
                        value_enum = float(request.POST["%s[%s][%s]" % ((key % (i, "subparams")), k, "value")])
                        print(text_enum, value_enum)
                        vfe = ValuesForEnum(enum=en, enum_key=text_enum, enum_value=value_enum)
                        vfe.save()
                        print(vfe)
                        k += 1
                    except Exception as e:
                        print(e)
                        break
                i += 1
            except Exception as e:
                print(e)
                break
        Criterion.objects.create(competition=comp, name='Итоговый', description='Итоговый критерий',
                                 result_formula=True)
        return JsonResponse({"comp_id": comp.id})
    return render(request, 'fls/add_comp_first.html', {"form": form})


@login_required(login_url="login/")
def comp_second_step(request, comp_id):
    comp = Competition.objects.get(id=comp_id)
    enums = CustomEnum.objects.filter(competition=comp)
    if request.method == 'POST':
        key = "params[%s][%s]"
        print(request.POST)
        i = 0
        while True:
            try:
                name = request.POST[key % (i, "name")]
                desc = request.POST[key % (i, "description")]
                c = Criterion(competition=comp, name=name, description=desc)
                c.save()
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
                        sub_p = Param(criterion=c, name=name_sub, type=type, for_formula=flag)
                        sub_p.save()
                        if type == 5:
                            enum_id = int(request.POST["%s[%s][%s]" % ((key % (i, "subparams")), k, "enum_id")])
                            sub_p.enum = CustomEnum.objects.get(id=enum_id)
                        elif type == 1:
                            sub_p.max = int(request.POST["%s[%s][%s]" % ((key % (i, "subparams")), k, "max")])
                        sub_p.save()
                        print(name_sub)
                        k += 1
                    except Exception as e:
                        print(e)
                        break
                if k == 1:
                    for jury in CustomUser.objects.filter(role=2):
                        WeightParamJury.objects.create(jury=jury, param=sub_p, weight_value=1)
                i += 1
            except Exception as e:
                print(e)
                break
    return render(request, 'fls/add_comp_second.html', {"types": TYPE_PARAM, "comp": comp, "enums": enums})


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
    criteria = Criterion.objects.filter(competition=comp, result_formula=False)
    collection = []
    for cr in criteria:
        params = Param.objects.filter(criterion=cr)
        collection.append({"param": cr, "subparams": params})
    if request.method == 'POST':
        print(request.POST)
        req = Request(competition=comp, participant=participant)
        req.save()
        for c in collection:
            for param in c["subparams"]:
                sp_val = ParamValue(param=param, request=req)
                sp_val.save()
                if param.type == 3 or param.type == 4:
                    print(request.FILES)
                    for f, h in zip(request.FILES.getlist("file_%s" % param.id), request.POST.getlist(
                            "header_%s" % param.id)):
                        print(f)
                        link_file = "%s/%s/%s.%s" % (
                            participant.id, comp_id, int(time.time() * 1000), f.name.split(".")[1])
                        fs = FileSystemStorage()
                        filename = fs.save(link_file, f)
                        u = UploadData(header_for_file=h, sub_param_value=sp_val)
                        if param.type == 4:
                            u.image = filename
                        else:
                            u.file = filename
                        u.save()
                else:
                    val = request.POST["sp_%s" % param.id]
                    if param.type == 1:
                        sp_val.value = val
                    elif param.type == 2 or param.type == 6:
                        sp_val.text = val
                    else:
                        sp_val.enum_val = ValuesForEnum.objects.get(id=val)
                    sp_val.save()

        print("saving")
        return redirect("fls:profile")

    return render(request, 'fls/load_request.html', {"comp": comp, "collection": collection})


def make_pairs(objects):
    params_modif = {}
    for p in objects:
        arr = []
        for f in objects:
            arr.append("%s_%s" % (p.id, f.id))
        params_modif[p.name] = arr
    return params_modif


def make_pair_matrix(values):
    criterion_rows = {}
    for key in values:
        param_id = key.split('_')[0].replace('rank', '')
        if not param_id in criterion_rows:
            criterion_rows[param_id] = [0.5]
        criterion_rows[param_id].append(float(values[key][0]))
    return criterion_rows


@login_required(login_url="login/")
def pairwise_comparison(request, comp_id):
    jury = CustomUser.objects.get(user=request.user)
    # пока для организатора, возможно эксперт нужен какой-то
    if jury.role != 3:
        return HttpResponse("Данная страница для Вас недоступна")
    comp = Competition.objects.get(id=comp_id)
    criteria = Criterion.objects.filter(competition=comp, result_formula=False)
    criteria_modif = make_pairs(criteria)

    if request.method == 'POST':
        values = dict(request.POST)
        del values['csrfmiddlewaretoken']
        criterion_rows = make_pair_matrix(values)
        elems = sum(criterion_rows.values(), [])
        for key in criterion_rows:
            criterion = Criterion.objects.get(id=int(key))
            criterion.weight_value = sum(criterion_rows[key]) / sum(elems)
            criterion.save()
        return redirect("fls:get_comp", comp_id)
    return render(request, 'fls/pairwise_comparison_table.html', {"params": criteria_modif, "comp": comp})


def pairwise_comparison_param(request, crit_id):
    jury = CustomUser.objects.get(user=request.user)
    if jury.role != 2:
        return HttpResponse("Данная страница для Вас недоступна")
    params = Criterion.objects.get(id=crit_id).param_criterion.filter(type__in=(1, 3, 4, 5))
    params_modif = make_pairs(params)
    criterion = Criterion.objects.get(id=crit_id)
    response = render(request, 'fls/pairwise_comparison_table.html', {"params": params_modif, 'crit': criterion})
    if request.method == 'POST':
        values = dict(request.POST)
        del values['csrfmiddlewaretoken']
        print(values)
        criterion_rows = make_pair_matrix(values)
        elems = sum(criterion_rows.values(), [])
        for key in criterion_rows:
            param = Param.objects.get(id=int(key))
            param_value = sum(criterion_rows[key]) / sum(elems)
            if not WeightParamJury.objects.filter(param=param, jury=jury).exists():
                WeightParamJury.objects.create(param=param, weight_value=param_value, jury=jury)
            else:
                w = WeightParamJury.objects.get(param=param, jury=jury)
                w.value = param_value
                w.save()
        response = redirect("fls:profile")
    return response


@login_required(login_url="login/")
def profile(request):
    user = CustomUser.objects.get(user=request.user)
    requests = Request.objects.filter(participant=user)
    new_requests = []
    view_requests = []
    new_criterions = []
    view_criterions = []
    select_comp = 0
    if request.method == "POST":
        comp_id = request.POST['comp']
        requests = Request.objects.filter(competition=Competition.objects.get(id=comp_id))
        criterions = Competition.objects.get(id=comp_id).competition_criterions.filter(result_formula=False)
        for req in requests:
            if EstimationJury.objects.filter(type=1, jury=user, request=req,
                                             criterion__result_formula=False).count() == len(criterions):
                view_requests.append(req)
            else:
                new_requests.append(req)
        for crit in criterions:
            if crit.param_criterion.count() > 1:
                if WeightParamJury.objects.filter(jury=user, param__criterion=crit).exists():
                    view_criterions.append(crit)
                else:
                    new_criterions.append(crit)
    return render(request, "fls/profile.html",
                  {"cust_user": user, "requests": requests, 'comps': user.competitions_for_jury.all(),
                   'new_requests': new_requests, 'view_requests': view_requests, 'select_comp': select_comp,
                   'statuses': STATUSES, 'new_crits': new_criterions, 'view_crits': view_criterions})


def ajax_comp_status(request):
    status = request.GET["status"]
    user = CustomUser.objects.get(user=request.user)
    comps = user.organizer_for_comp.all().filter(status=status)
    return JsonResponse(
        {'est': render_to_string('fls/part_organizer_profile.html', {"org_comps": comps, "statuses": STATUSES,
                                                                     "selected_status": int(status)})})


def login_view(request):
    if not request.user.is_anonymous:
        return redirect("fls:profile")

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


@login_required(login_url="login/")
def get_request(request, id):
    cur_request = Request.objects.get(id=id)
    estimate = EstimationJury.objects.filter(request=cur_request, jury=request.user.custom_user)
    flag = False
    flag_for_jury = False
    if CustomUser.objects.get(user=request.user) in cur_request.competition.jurys.all():
        flag_for_jury = True
    arr = []
    criteria = Criterion.objects.filter(competition=cur_request.competition, result_formula=False)
    if len(estimate) > 0:
        flag = True
    for c in criteria:
        subvalues = []
        for sb in c.param_criterion.all():
            sbvalue = ParamValue.objects.get(param=sb, request=cur_request)
            subvalues.append(sbvalue)
        est = 0
        if flag:
            est = estimate.filter(criterion=c)[0].value
        arr.append((c, subvalues, est))
    print(dict)
    return render(request, 'fls/request.html',
                  {'request': cur_request, 'values': arr, 'user': CustomUser.objects.get(user=request.user),
                   'estimate_flag': flag, 'flag': flag_for_jury})


def estimate_req(request, req_id):
    req = Request.objects.get(id=req_id)
    criteria = req.competition.competition_criterions.all().filter(result_formula=False)
    final_criteria = req.competition.competition_criterions.get(result_formula=True)
    jury = CustomUser.objects.get(user=request.user)
    if request.method == "POST":
        jury_final_estimate = 0
        for c in criteria:
            val = request.POST["est_val_%s" % c.id]
            estimate = EstimationJury.objects.filter(jury=jury,
                                                     request=req, type=1, criterion=c)
            if len(estimate) > 0:
                estimate = estimate[0]
                estimate.value = val
            else:
                estimate = EstimationJury(jury=jury,
                                          request=req, criterion=c, value=val, type=1)
            estimate.save()

            jury_final_estimate += c.weight_value * float(val)

        final_estimate = EstimationJury.objects.filter(jury=jury, request=req,
                                                       type=1,
                                                       criterion=final_criteria)
        if final_estimate.exists():
            final_estimate = final_estimate[0]
            final_estimate.value = jury_final_estimate
        else:
            final_estimate = EstimationJury(jury=jury, request=req, type=1, criterion=final_criteria,
                                            value=jury_final_estimate)
        final_estimate.save()

    return redirect("fls:get_request", req_id)


def estimate_del(request, req_id):
    estimate = EstimationJury.objects.filter(request=Request.objects.get(id=req_id),
                                             jury=CustomUser.objects.get(user=request.user))
    estimate.delete()
    return redirect("fls:get_request", req_id)


def get_comp(request, id):
    comp = Competition.objects.get(id=id)
    user = CustomUser.objects.get(user=request.user)
    requests = Request.objects.filter(competition=Competition.objects.get(id=id))
    return render(request, 'fls/comp.html', {'comp': comp, 'user': user, 'requests': requests})


@login_required(login_url="login/")
def similar_jury_page(request, comp_id=None):
    comps = Competition.objects.filter(status=4, organizer=request.user.custom_user, method_of_estimate=1)
    selected_comp_id = int(comp_id) if comp_id else None
    return render(request, 'fls/sim_jury/sim_jury.html', {'comps': comps, 'selected_comp_id': selected_comp_id})


# @login_required(login_url="login/")
# def similar_jury(request):
#     comp_id, type, jury_id, crit_id = int(request.GET['comp']), int(request.GET['type']), int(request.GET['jury']), int(
#         request.GET['crit'])
#     reqs = Request.objects.filter(competition_id=comp_id)
#     slt_jury = CustomUser.objects.get(id=jury_id)
#     slt_ests = make_ranks(
#         [EstimationJury.objects.get(jury=slt_jury, type=type, request=req, criterion_id=crit_id).value for req in reqs])
#     rest_jury = CustomUser.objects.filter(role=2).exclude(id=jury_id)
#     smt = {}
#     jury_ests = {}
#     for jury in rest_jury:
#         s = 0
#         jury_ests[jury.id] = []
#         for req in reqs:
#             slt_value = EstimationJury.objects.get(jury=slt_jury, type=type, request=req, criterion_id=crit_id).value
#             jury_value = EstimationJury.objects.get(jury=jury, type=type, request=req, criterion_id=crit_id).value
#             jury_ests[jury.id].append(jury_value)
#             s += abs(slt_value - jury_value)
#         jury_ests[jury.id] = make_ranks(jury_ests[jury.id])
#         smt[jury.id] = round(s, 2)
#     print('smt', smt)
#     if request.GET['key'] == 'est':
#         sorted_smt = dict(sorted(smt.items(), key=lambda item: item[1]))
#     else:
#         sorted_kemeni = {key: dist_kemeni(slt_ests, jury_ests[key]) for key in smt}
#         sorted_smt = dict(sorted(sorted_kemeni.items(), key=lambda item: item[1]))
#
#     print('sorted_smt', sorted_smt)
#     clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(list(sorted_smt.keys()))])
#     ordering = 'CASE %s END' % clauses
#     sorted_jury = CustomUser.objects.filter(pk__in=list(sorted_smt.keys())).extra(
#         select={'ordering': ordering}, order_by=('ordering',))
#     print(sorted_jury)
#     estimation_values = {}
#     for i, req in enumerate(reqs):
#         part_name = req.participant
#         estimation_values[part_name] = []
#         estimation_values[part_name].append((
#             round(EstimationJury.objects.get(type=type, jury=slt_jury, request=req, criterion_id=crit_id).value, 2),
#             slt_ests[i]))
#         estimation_values[part_name].extend(
#             [(round(EstimationJury.objects.get(type=type, jury=jury, request=req, criterion_id=crit_id).value, 2),
#               jury_ests[jury.id][i]) for
#              jury in sorted_jury])
#     diff = sorted_smt.values()
#     est_key = request.GET['key'] == 'est'
#     data = {'est': render_to_string('fls/sim_jury/table.html',
#                                     {'ests': estimation_values, 'jurys': sorted_jury,
#                                      'slt_jury': slt_jury, 'diffs': diff, 'est_key': est_key})}
#     return JsonResponse(data)


@login_required(login_url="login/")
def metcomp_page(request, comp_id=None):
    comps = Competition.objects.filter(status=4, organizer=request.user.custom_user, method_of_estimate=1)
    selected_comp_id = int(comp_id) if comp_id else None
    return render(request, 'fls/metcomp/metcomp.html', {'comps': comps, 'selected_comp_id': selected_comp_id})


def method_comparison(request):
    methods = (1, 2)
    comp_id, jury_id, crit_id = int(request.GET['comp']), int(request.GET['jury']), int(request.GET['crit'])
    slt_jury = CustomUser.objects.get(id=jury_id)
    reqs = Request.objects.filter(competition_id=comp_id)
    estimation_values = {}
    for req in reqs:
        part_name = req.participant
        estimation_values[part_name] = [[], []]
        estimation_values[part_name][1].extend(
            round(EstimationJury.objects.get(request=req, jury=slt_jury, type=type, criterion_id=crit_id).value, 2) for
            type in methods)
        diff = round((estimation_values[part_name][1][0] - estimation_values[part_name][1][1]), 2)
        estimation_values[part_name].append(diff)
    data = {'est': render_to_string('fls/metcomp/table.html',
                                    {'ests': estimation_values,
                                     'slt_jury': slt_jury})}

    return JsonResponse(data)


@login_required(login_url="login/")
def deviations_page(request, comp_id=None):
    comps = Competition.objects.filter(status=4, organizer=request.user.custom_user, method_of_estimate=1)
    selected_comp_id = int(comp_id) if comp_id else None
    return render(request, 'fls/dev/dev.html', {'comps': comps, 'selected_comp_id': selected_comp_id})


@login_required(login_url="login/")
def est_deviations(request):
    comp_id, req_id, crit_id = int(request.GET['comp']), int(request.GET['reqs']), int(request.GET['crit'])
    req = Request.objects.get(id=req_id)
    jurys = Competition.objects.get(id=comp_id).jurys.all()
    avg_est = sum([jury_est.value for jury_est in
                   EstimationJury.objects.filter(request=req, type=1, criterion_id=crit_id)]) / len(jurys)
    jury_est_values = {}
    for jury in jurys:
        jury_est_values[jury] = []
        jury_est = EstimationJury.objects.get(jury=jury, type=1, request=req, criterion_id=crit_id).value
        jury_est_values[jury].extend([round(jury_est, 2), round((jury_est - avg_est), 2)])
    jury_est_values = sorted(jury_est_values.items(), key=lambda item: item[1][1], reverse=True)
    avg_dev = math.sqrt(sum([dev[1][1] ** 2 for dev in jury_est_values]) / len(jury_est_values))
    print(jury_est_values)
    variation_coef = avg_dev / avg_est
    data = {'est': render_to_string('fls/dev/table.html',
                                    {'ests': jury_est_values, 'comm': round(avg_est, 2),
                                     'avg_dev': round(avg_dev, 2), 'var_coef': round(variation_coef, 2)})}
    return JsonResponse(data)


def comp_reqs(request):
    comp = Competition.objects.get(id=request.GET['comp'])
    reqs = comp.competition_request.all()
    criterions = comp.competition_criterions.all()
    data = {'reqs': render_to_string('fls/dev/reqs.html', {'reqs': reqs}),
            'crits': render_to_string('fls/sim_jury/criterions.html', {'criterions': criterions})}
    return JsonResponse(data)


def change_status(request, id, val):
    comp = Competition.objects.get(id=id)
    if comp.method_of_estimate == 1 and int(val) == 4:
        calculate_jury_automate_ests(id)
        define_optimal_k(id)
    comp.status = int(val)
    comp.save()
    return redirect("fls:get_comp", id)


@login_required(login_url="login/")
def coherence_page(request, comp_id=None):
    comps = Competition.objects.filter(status=4, organizer=request.user.custom_user, method_of_estimate=1)
    selected_comp_id = int(comp_id) if comp_id else None
    return render(request, 'fls/coher/coher.html', {'comps': comps, 'selected_comp_id': selected_comp_id})


@login_required(login_url="login/")
def coherence(request):
    comp_id, clusts, crit_id = int(request.GET['comp']), int(request.GET['clusts']), int(request.GET['crit']),
    comp = Competition.objects.get(id=comp_id)
    reqs = comp.competition_request.all()
    jurys = comp.jurys.all()
    jury_ranks = {}
    for jury in jurys:
        jury_ranks[jury] = make_ranks(
            [EstimationJury.objects.get(type=1, jury=jury, request=req, criterion_id=crit_id).value for req in reqs],
            method='average',
            related_rank_groups=True)
    req_values = {}
    for idx, req in enumerate(reqs):
        req_values[req] = sum([jury_ranks[jury][0][idx] for jury in jurys])

    common_rank_req_sum_avg = sum(list(req_values.values())) / len(reqs)
    dev_sum = 0
    for req in req_values:
        dev_sum += (req_values[req] - common_rank_req_sum_avg) ** 2
    sum_T = 0
    for jury in jury_ranks:
        sum_T += sum([el ** 3 - el for el in jury_ranks[jury][1]])
    kendall_coef = round((12 * dev_sum / ((len(jurys) ** 2) * (len(reqs) ** 3 - len(reqs)) - len(jurys) * sum_T)),
                         2)

    jury_rankings = [make_ranks(
        [EstimationJury.objects.get(type=1, jury=jury, request=req, criterion_id=crit_id).value for req in reqs],
        method='min') for
        jury in jurys]
    clusters, centroids, labels = clusterization(jury_rankings, clusts)
    for label in clusters:
        clusters[label].insert(0, centroids[label])
    clusters_jury = {}
    for idx, label in enumerate(labels):
        if not label in clusters_jury:
            clusters_jury[label] = []
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


@login_required(login_url="login/")
def comp_criterions_jurys(request):
    comp = Competition.objects.get(id=request.GET['comp'])
    criterions = comp.competition_criterions.all()
    jurys = comp.jurys.all()
    data = {'crits': render_to_string('fls/sim_jury/criterions.html', {'criterions': criterions}),
            'jury': render_to_string('fls/sim_jury/jury.html', {'jurys': jurys})}
    return JsonResponse(data)


@login_required(login_url="login/")
def optimal_k_for_criterion(request):
    crit_id = int(request.GET['crit'])
    ks = list(ClusterNumber.objects.filter(criterion_id=crit_id, type=1).values_list('k_number', flat=True))
    k_range = [(k, 1) for k in ks]
    # k_range.extend([(k, 0) for k in range(1, len(jurys)) if k not in ks])
    # print(k_range)
    data = {'k_range': render_to_string('fls/coher/k_range.html', {'k_range': k_range})}
    return JsonResponse(data)


def info_est_jury(request, id):
    comp = Competition.objects.get(id=id)
    jurys = comp.jurys.all()
    requests = comp.competition_request.all()
    len_req = len(requests)
    result = []
    for jury in jurys:
        sum = 0
        for req in requests:
            if EstimationJury.objects.filter(request=req, jury=jury).count() > 0:
                sum += 1
        result.append((jury, round((sum * 100 / len_req), 2)))
    return render(request, "fls/est_info_jury.html", {"result": result, "comp": comp})


def inv_change_status(request, id, status):
    status = int(status)
    invitation = Invitation.objects.get(id=id)
    if status == 2:
        invitation.status = status
        invitation.save()
        invitation.competition.jurys.add(invitation.jury)
    if status == 3:
        invitation.status = status
        invitation.save()
    return redirect("fls:profile")


def delete_req(request, id):
    request = Request.objects.get(id=id)
    path = None
    for pv in request.request_param_values.all():
        for f in pv.files.all():
            if pv.param.type == 3:
                path = '{}{}'.format(BASE_DIR, f.file.url).replace('\\', '/').replace('//', '/')
            else:
                path = '{}{}'.format(BASE_DIR, f.image.url).replace('\\', '/').replace('//', '/')
            if os.path.exists(path):
                os.remove(path)
            f.delete()
            print("delete photo or file")
    if path is not None:
        os.rmdir(os.path.dirname(path))
    request.delete()
    print("request deleted")
    return redirect("fls:profile")



@login_required(login_url="login/")
def similar_jury(request):
    comp_id, jury_id, crit_id = int(request.GET['comp']), int(request.GET['jury']), int(request.GET['crit'])
    reqs = Request.objects.filter(competition_id=comp_id)
    slt_jury = CustomUser.objects.get(id=jury_id)
    slt_ests = make_ranks(
        [EstimationJury.objects.get(jury=slt_jury, type=1, request=req, criterion_id=crit_id).value for req in reqs])
    max_dist = max_dist_kemeni_for_ranking(slt_ests)
    rest_jury = Competition.objects.get(id=comp_id).jurys.exclude(id=jury_id)
    smt = {}
    jury_ests = {}
    for jury in rest_jury:
        s = 0
        jury_ests[jury.id] = []
        for req in reqs:
            slt_value = EstimationJury.objects.get(jury=slt_jury, type=1, request=req, criterion_id=crit_id).value
            print(jury.id, req.id)
            jury_value = EstimationJury.objects.get(jury=jury, type=1, request=req, criterion_id=crit_id).value
            jury_ests[jury.id].append(jury_value)
            s += abs(slt_value - jury_value)
        jury_ests[jury.id] = make_ranks(jury_ests[jury.id])
        smt[jury.id] = int(s)
    print('smt', smt)

    sorted_kemeni = {key: (round((dist_kemeni(slt_ests, jury_ests[key]) / max_dist), 2), smt[key]) for key in smt}
    sorted_smt = dict(sorted(sorted_kemeni.items(), key=lambda item: item[1][0]))

    print('sorted_smt', sorted_smt)
    clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(list(sorted_smt.keys()))])
    ordering = 'CASE %s END' % clauses
    sorted_jury = CustomUser.objects.filter(pk__in=list(sorted_smt.keys())).extra(
        select={'ordering': ordering}, order_by=('ordering',))
    print(sorted_jury)
    estimation_values = {}
    for i, req in enumerate(reqs):
        part_name = req.participant
        estimation_values[part_name] = []
        estimation_values[part_name].append((
            round(EstimationJury.objects.get(type=1, jury=slt_jury, request=req, criterion_id=crit_id).value, 2),
            slt_ests[i]))
        estimation_values[part_name].extend(
            [(round(EstimationJury.objects.get(type=1, jury=jury, request=req, criterion_id=crit_id).value, 2),
              jury_ests[jury.id][i]) for
             jury in sorted_jury])
    dists = sorted_smt.values()
    data = {'est': render_to_string('fls/sim_jury/table.html',
                                    {'ests': estimation_values, 'jurys': sorted_jury,
                                     'slt_jury': slt_jury, 'dists': dists})}
    return JsonResponse(data)

def same_criteria_importance(request, comp_id):
    comp = Competition.objects.get(id=comp_id)
    criteria = comp.competition_criterions.all().filter(result_formula=False)
    val = 1 / len(criteria)
    for criterion in criteria:
        criterion.weight_value = val
        criterion.save()
    return redirect("fls:get_comp", comp_id)
