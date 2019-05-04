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

from fls.models import CriterionValue, Request, CustomUser, EstimationJury, Competition, ParamValue, WeightParamJury

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
    return list(map(int, median))


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


def distance(elem1, elem2):
    return dist_kemeni(elem1, elem2)


def same(prev, pres):
    for i, j in zip(prev, pres):
        if i != j:
            return False
    return True


def define_centers(dataset, n):
    centers = [dataset[0]]
    for i in range(1, n):
        dist_list = []
        for ranking in dataset:
            dist = [distance(ranking, center) for center in centers]
            min_dist = min(dist)
            dist_list.append(min_dist)
        centers.append(dataset[dist_list.index(max(dist_list))])
    return centers


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
    return labels, centroids



def normalize_crit_values(crit):
    reqs = crit.competition.competition_request.all()
    params = crit.param_criterion.filter(type__in=(1, 3, 4, 5))
    req_param_values = []
    for req in reqs:
        req_values = []
        for param in params:
            if param.type == 1:
                value = ParamValue.objects.get(param=param, request=req).value
                req_values.append(value)
            elif param.type == 5:
                req_values.append(ParamValue.objects.get(param=param, request=req).enum_val.enum_value)
            else:
                req_values.append(ParamValue.objects.get(param=param, request=req).get_files().count())
        req_param_values.append(req_values)
    req_param_values = np.array(req_param_values)
    for i in range(len(params)):
        max_v, min_v = np.max(req_param_values[:, i]), np.min(req_param_values[:, i])
        for k in range(len(reqs)):
            req_param_values[k, i] = 1 + (req_param_values[k, i] - min_v) / (max_v - min_v) * (crit.max_for_jury-1)
    return req_param_values, reqs, params


def aut_est_jury(jury, crit):
    req_param_values, reqs, params = normalize_crit_values(crit)
    for i, req in enumerate(reqs):
        sum_value = 0
        for j, param in enumerate(params):
            weight_value = WeightParamJury.objects.get(jury=jury, param=param).weight_value
            param_value = ParamValue.objects.get(param=param, request=req).value
            sum_value += param_value * weight_value
        if EstimationJury.objects.filter(jury=jury, type=2, request=req, criterion=crit).exists():
            estimaion_jury = EstimationJury.objects.get(jury=jury, type=2, request=req, criterion=crit)
            estimaion_jury.value = sum_value
            estimaion_jury.save()
        else:
            EstimationJury.objects.create(jury=jury, type=2, request=req, criterion=crit, value=sum_value)
