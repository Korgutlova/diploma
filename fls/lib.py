import math
import sys
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

from fls.models import EstimationJury, Competition, ParamValue, WeightParamJury, \
    Criterion, ClusterNumber

from math import log, sqrt

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


# parse_formula("5*a_0 + func1(a_1, a_2)/log(a_3)", [2, 8, 7, 5])

def make_loss_matrix(rankings):
    n_reqs, n_experts = len(rankings[0]), len(rankings)
    matrixes = [make_matrix(ranking) for ranking in rankings]
    loss_matrix = np.empty(shape=(n_reqs, n_reqs))
    for i in range(n_reqs):
        for j in range(n_reqs):
            loss_matrix[i, j] = 0
            for k in range(n_experts):
                loss_matrix[i, j] += 1 - matrixes[k][i, j]
    return loss_matrix


def median_kemeni(rankings):
    loss_matrix = make_loss_matrix(rankings)
    n_requests = loss_matrix.shape[0]
    indexes, ranks = list(range(0, n_requests)), []
    pen_matrix = deepcopy(loss_matrix)
    while not pen_matrix.size == 0:
        row_sums = np.sum(pen_matrix, axis=1)
        request_idx = np.argmin(row_sums)
        ranks.append(indexes[request_idx])
        indexes.pop(request_idx)
        pen_matrix = np.delete(pen_matrix, request_idx, axis=0)
        pen_matrix = np.delete(pen_matrix, request_idx, axis=1)
    for k in range(n_requests - 2, -1, -1):
        if loss_matrix[ranks[k], ranks[k + 1]] > loss_matrix[ranks[k + 1], ranks[k]]:
            ranks[k], ranks[k + 1] = ranks[k + 1], ranks[k]
    median = np.empty(shape=(n_requests))
    for i, request_idx in enumerate(ranks):
        median[request_idx] = i + 1
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


def make_inverse_matrix(matrix):
    length = matrix.shape[0]
    inverse_matrix = np.empty(shape=(length, length))
    for i in range(length):
        for j in range(i, length):
            if i != j:
                if matrix[i, j] == 1:
                    inverse_matrix[i, j] = -1
                    inverse_matrix[j, i] = 1
                elif matrix[i, j] == 0:
                    inverse_matrix[i, j] = 1
                    inverse_matrix[j, i] = -1
            else:
                inverse_matrix[i, j] = 0
    return inverse_matrix


def max_dist_kemeni_for_ranking(ranking):
    matrix = make_matrix(ranking)
    inverse_matrix = make_inverse_matrix(matrix)
    diff_matrix = matrix - inverse_matrix
    return int(np.sum(np.absolute(diff_matrix)))


def make_ranks(estimations, method='min', related_rank_groups=False):
    ranks = list(rankdata([-1 * e for e in estimations], method=method))
    rank_counts_in_related_groups = [ranks.count(rank) for rank in set(ranks) if ranks.count(rank) > 1]
    return (ranks, rank_counts_in_related_groups) if related_rank_groups else ranks


def distance(elem1, elem2):
    if not elem2:
        return sys.maxsize
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
            try:
                centroids[i] = median_kemeni(cluster_rankings)
            except:
                pass
    clusters = {}
    for idx, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(dataset[idx])

    return clusters, centroids, labels



def generate_reference_datasets(B, dataset):
    B_datasets = []
    n_objects = len(dataset)
    n_features = len(dataset[0])
    for i in range(B):
        b_dataset = []
        for j in range(n_objects):
            b_dataset.append(list(np.random.permutation(range(1, n_features + 1))))
        B_datasets.append(b_dataset)
    return B_datasets


def define_optimal_k_number(dataset):
    clusters = clusterization(dataset, 2)[0]
    if len(dataset) == 2:
        return [len(clusters.keys())]
    if len(clusters.keys()) == 1:
        return [1]

    W_k_values = []
    B = 10
    Gap = []
    sk = []
    reference_dataset = generate_reference_datasets(B, dataset)
    for k in range(2, len(dataset)):
        clusters = clusterization(dataset, k)[0]
        W_k_value = 0
        D_r = 0
        for label in clusters:
            for elem1 in clusters[label]:
                for elem2 in clusters[label]:
                    D_r += dist_kemeni(elem1, elem2)
            W_k_value += D_r / (2 * len(clusters[label]))
        W_k_values.append(W_k_value)
        b_W_k_values = []
        for ref_dataset in reference_dataset:
            clusters = clusterization(ref_dataset, k)[0]
            W_k = 0
            D_r = 0
            for label in clusters:
                for elem1 in clusters[label]:
                    for elem2 in clusters[label]:
                        D_r += dist_kemeni(elem1, elem2)
                W_k += D_r / (2 * len(clusters[label]))
            b_W_k_values.append(W_k)

        try:
            Gap.append(sum([log(float(b_w_k)) for b_w_k in b_W_k_values]) / B - log(W_k_value))
            w_k = sum([log(b_w_k) for b_w_k in b_W_k_values]) / B
            s_k = sqrt(sum([(log(b_w_k) - w_k) ** 2 for b_w_k in b_W_k_values]) / B) * sqrt(1 + 1 / B)
            sk.append(s_k)
        except:

            Gap.append(-1000)
            sk.append(0)
    print(W_k_values)
    print(sk)
    print(Gap)
    if Gap.count(-1000) == len(Gap):
        return [2]
    result_k = []
    for i in range(len(Gap) - 1):
        if Gap[i] != -1000 and Gap[i] >= (Gap[i + 1] - sk[i + 1]):
            result_k.append(i + 2)
            if len(result_k) >= 2:
                break
    return result_k


def normalize_crit_params_values(criterion):
    reqs = criterion.competition.competition_request.all()
    params = criterion.param_criterion.filter(type__in=(1, 3, 4, 5))
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
            req_param_values[k, i] = (req_param_values[k, i] - min_v) / (
                    max_v - min_v) * criterion.competition.max_for_criteria
    return req_param_values, reqs, params


def jury_weight_sum_ests(jury, crit, req_param_values, reqs, params):
    for i, req in enumerate(reqs):
        sum_value = 0
        for j, param in enumerate(params):
            weight_value = WeightParamJury.objects.get(jury=jury, param=param).weight_value
            param_value = req_param_values[i, j]
            sum_value += param_value * weight_value
        if EstimationJury.objects.filter(jury=jury, type=2, request=req, criterion=crit).exists():
            estimaion_jury = EstimationJury.objects.get(jury=jury, type=2, request=req, criterion=crit)
            estimaion_jury.value = sum_value
            estimaion_jury.save()
        else:
            EstimationJury.objects.create(jury=jury, type=2, request=req, criterion=crit, value=sum_value)


def calculate_jury_automate_ests(comp_id):
    comp = Competition.objects.get(id=comp_id)
    jurys = comp.jurys.all()
    final_criterion = Criterion.objects.get(competition=comp, result_formula=True)
    criterions = Competition.objects.get(id=comp_id).competition_criterions.filter(result_formula=False)
    for crit in criterions:
        req_param_values, reqs, params = normalize_crit_params_values(crit)
        for jury in jurys:
            jury_weight_sum_ests(jury, crit, req_param_values, reqs, params)
    reqs = Competition.objects.get(id=comp_id).competition_request.all()
    for jury in jurys:
        for req in reqs:
            final_jury_value = 0
            for crit in criterions:
                final_jury_value += EstimationJury.objects.get(jury=jury, request=req, criterion=crit,
                                                               type=2).value * crit.weight_value
            if not EstimationJury.objects.filter(jury=jury, request=req, criterion=final_criterion, type=2).exists():
                EstimationJury.objects.create(jury=jury, request=req, criterion=final_criterion, type=2,
                                              value=final_jury_value)
            else:
                estimate = EstimationJury.objects.get(jury=jury, request=req, criterion=final_criterion, type=2)
                estimate.value = final_jury_value
                estimate.save()


def define_optimal_k(comp_id):
    comp = Competition.objects.get(id=comp_id)
    reqs = comp.competition_request.all()
    criterions = comp.competition_criterions.all()
    jurys = comp.jurys.all()
    for criterion in criterions:
        for type in (1, 2):
            jury_rankings = [make_ranks(
                [EstimationJury.objects.get(type=type, jury=jury, request=req, criterion=criterion).value for req in
                 reqs],
                method='min') for
                jury in jurys]
            result_k = define_optimal_k_number(jury_rankings)
            ClusterNumber.objects.filter(criterion=criterion, type=type).delete()
            for k in result_k:
                ClusterNumber.objects.create(criterion=criterion, type=type, k_number=k)


