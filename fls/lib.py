import math
from copy import deepcopy
from itertools import permutations

import cexprtk
import django
import os

import numpy as np
from scipy.stats import rankdata

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dipl.settings")
django.setup()

from py_expression_eval import Parser

from fls.models import CriterionValue, ParamValue, Request, CustomUser, WeightParamJury, EstimationJury, \
    RequestEstimation, Competition

parser = Parser()


# типовая
def func1(a, b):
    return float(math.log(a, 2)) / (b + 53)


def parse_formula(formula, params_values):
    vars_func = parser.parse(formula).variables()
    print(vars_func)
    vars = list(filter(lambda x: x.find('_') != -1, vars_func))
    print(vars)
    funcs = list(filter(lambda x: x.find('_') == -1, vars_func))
    print(funcs)
    variables = {}
    for var in vars:
        variables[var] = params_values[int(var.split('_')[1])]
    print(variables)
    st = cexprtk.Symbol_Table(variables)
    for func in funcs:
        st.functions[func] = globals()[func]
    calc_exp = cexprtk.Expression(formula, st)
    print(calc_exp())
    return calc_exp()


parse_formula("5*a_0 + func1(a_1, a_2)/log(a_3)", [2, 8, 7, 5])

MAIN_DICTIONARY = {"a_11": 2, "a_23": 8, "a_21": 7, "a_31": 5}


def custom_parse_formula(formula):
    vars_func = parser.parse(formula).variables()
    print(vars_func)
    vars = list(filter(lambda x: x.find('_') != -1, vars_func))
    # исходя из id будет вытягиваться соответсвующий subпараметр value заявки и формироваться такой словарь MAIN_DICTIONARY
    funcs = list(filter(lambda x: x.find('_') == -1, vars_func))
    print(funcs)
    st = cexprtk.Symbol_Table(MAIN_DICTIONARY)
    for func in funcs:
        st.functions[func] = globals()[func]
    calc_exp = cexprtk.Expression(formula, st)
    print(calc_exp())
    return calc_exp()


custom_parse_formula("5*a_11 + func1(a_23, a_21)/log(a_31)")


# parse_formula("5*a_0 + func1(a_1, a_2)/log(a_3)", [2, 8, 7, 5])
# perms = list(permutations(range(1, len(rankings[0]) + 1)))
# dist_sums = []
# for perm in perms:
#     sum = 0
#     for ranking in rankings:
#         sum += dist_kemeni(perm, ranking)
#     dist_sums.append(sum)
#
# return perms[dist_sums.index(min(dist_sums))]


def median_kemeni(rankings):
    n_reqs = len(rankings[0])
    n_jury = len(rankings)
    matrixes = [make_matrix(ranking) for ranking in rankings]
    loss_matrix = np.empty(shape=(n_reqs, n_reqs))
    indexes = list(range(0, n_reqs))
    ranks = []
    for i in range(n_reqs):
        for j in range(n_reqs):
            loss_matrix[i, j] = 0
            for k in range(n_jury):
                loss_matrix[i, j] += 1 - matrixes[k][i, j]
    pen_matrix = deepcopy(loss_matrix)
    while not pen_matrix.size == 0:
        row_sums = np.sum(pen_matrix, axis=1)
        idx = np.argmin(row_sums)
        ranks.append(indexes[int(idx)])
        indexes.pop(int(idx))
        pen_matrix = np.delete(pen_matrix, idx, axis=0)
        pen_matrix = np.delete(pen_matrix, idx, axis=1)
    for k in range(n_reqs - 2, -1, -1):
        if loss_matrix[ranks[k], ranks[k + 1]] > loss_matrix[ranks[k + 1], ranks[k]]:
            ranks[k], ranks[k + 1] = ranks[k + 1], ranks[k]
    median = np.empty(shape=(n_reqs))
    for i, elem in enumerate(ranks):
        median[elem] = i + 1
    print('result', median)
    return list(median)


def dist_kemeni(ranking1, ranking2):
    matrix1, matrix2 = make_matrix(ranking1), make_matrix(ranking2)
    result_matrix = matrix1 - matrix2
    return int(np.sum(np.absolute(result_matrix)))


def make_matrix(ranking):
    length = len(ranking)
    matrix = np.empty(shape=(length, length))
    for i in range(length):
        for j in range(i, length):
            if ranking[i] < ranking[j]:
                matrix[i, j] = 1
                matrix[j, i] = -1
            elif ranking[i] == ranking[j]:
                matrix[i, j] = 0
                matrix[j, i] = 0
            else:
                matrix[i, j] = -1
                matrix[j, i] = 1
    return matrix


def make_ranks(values, method='min', s_m=False):
    ranks = list(rankdata([-1 * e for e in values], method=method))
    same_groups_count = [ranks.count(rank) for rank in set(ranks) if ranks.count(rank) > 1]

    return (ranks, same_groups_count) if s_m else ranks


# объединение оценок жюри для методов 1,3 по заданной (созданной/обновленной) формуле
# formula_for_jury - объект CalcEstimationJury
def union_jury_estimations(formula_for_jury):
    for req in formula_for_jury.competition.competition_request.all():
        union_request_ests(req, formula_for_jury)


def union_request_ests(req, formula_for_jury, types=(1, 3)):
    jurys = CustomUser.objects.filter(role=2)
    for type in types:
        jury_values = []
        for jury in jurys:
            jury_values.append(EstimationJury.objects.get(type=type, jury=jury, request=req).value)
        common_jury_value = parse_formula(formula_for_jury.formula, jury_values)
        if not RequestEstimation.objects.filter(request=req, jury_formula=formula_for_jury, type=type).exists():
            RequestEstimation.objects.create(type=type, request=req, value=common_jury_value,
                                             jury_formula=formula_for_jury)
        else:
            est = RequestEstimation.objects.get(type=type, request=req,
                                                jury_formula=formula_for_jury)
            est.value = common_jury_value
            est.save()


# для вызова после создания/обновления попар.кф. у жюри
def process_3_method(jury, comp):
    for req in comp.competition_request.all():
        process_3_method_request(req, jury)


def process_3_method_request(req, jury):
    params = req.competition.competition_params.all()
    jury_value = 0

    for param in params:
        param_value = ParamValue.objects.get(param=param, request=req).value
        weight = WeightParamJury.objects.get(type=3, param=param, jury=jury).value
        jury_value += weight * param_value

    if EstimationJury.objects.filter(type=3, request=req, jury=jury).exists():
        est = EstimationJury.objects.get(type=3, request=req, jury=jury)
        est.value = jury_value
        est.save()
    else:
        EstimationJury.objects.create(type=3, request=req, jury=jury, value=jury_value)


# для вызова после создания/обновления Criterion конкурса
def process_5_method(criterion):
    for req in criterion.competition.competition_request.all():
        process_5_method_request(req, criterion)


def process_5_method_request(req, criterion):
    param_values = []
    for param in criterion.competition.competition_params.all():
        param_values.append(ParamValue.objects.get(param=param, request=req).value)

    value = parse_formula(criterion.formula, param_values)
    if CriterionValue.objects.filter(criterion=criterion, request=req).exists():
        crit_value = CriterionValue.objects.get(criterion=criterion, request=req)
        crit_value.value = value
        crit_value.save()
    else:
        CriterionValue.objects.create(criterion=criterion, request=req, value=value)


# для всех подсчётов после создания/обновления заявки
def process_request(request_id, union_types=(1, 3)):
    req = Request.objects.get(id=request_id)
    for jury in CustomUser.objects.filter(role=2):
        process_3_method_request(req, jury)
    for criterion in req.competition.competition_criterions.all():
        process_5_method_request(req, criterion)
    for jury_formula in req.competition.competition_formula_for_jury.all():
        union_request_ests(req, jury_formula, union_types)


# process_requests(Competition.objects.get(id=8))

# print(dist_kemeni([3, 4, 2, 1], [1, 2, 4, 3]))

# print(median_kemeni([[1, 3, 2], [2, 1, 3], [3, 1, 2]]))

# print(make_ranks([3, 1, 2, 2], method='average', s_m=True))

# print(make_matrix([1, 2.5, 2.5, 3]))

def distance(elem1, elem2):
    return dist_kemeni(elem1, elem2)


def same(prev, pres):
    for i, j in zip(prev, pres):
        if i != j:
            return False
    return True


def define_centers(dataset, n):
    return [dataset[i] for i in range(n)]


def clusterization(dataset, n_clusters):
    labels = []
    centroids = define_centers(dataset, n_clusters)
    prev_centroids = [[0] * len(centroids[0]) for i in range(len(centroids))]

    while not same(prev_centroids, centroids):
        labels = []
        prev_centroids = deepcopy(centroids)
        for ranking in dataset:
            dists = [distance(ranking, center) for center in centroids]
            idx = dists.index(min(dists))
            labels.append(idx)
        for i in range(n_clusters):
            cluster_rankings = []
            for k, num_label in enumerate(labels):
                if num_label == i:
                    cluster_rankings.append(dataset[k])
            centroids[i] = median_kemeni(cluster_rankings)
    print(labels)


rankings = [
    [1, 3, 2, 4, 6, 5, 7],
    [3, 2, 1, 4, 5, 6, 7],
    [6, 4, 3, 5, 1, 2, 7],
    [1, 2, 3, 4, 6, 5, 7],
    [3, 2, 1, 5, 4, 6, 7],
    [6, 4, 3, 1, 5, 2, 7],
    [6, 4, 3, 5, 2, 1, 7]

]

clusterization(rankings, 3)

# clusterization(rankings, 3)

# median_kemeni(rankings)
