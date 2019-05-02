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

from fls.models import CriterionValue, Request, CustomUser, EstimationJury, Competition

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
#
# rankings = [
#     [6, 4, 3, 1, 5, 2, 7],
#     [6, 4, 3, 5, 2, 1, 7],
#     [1, 3, 2, 4, 6, 5, 7],
#     [1, 2, 3, 4, 6, 5, 7],
#     [3, 2, 1, 4, 5, 6, 7],
#     [6, 4, 3, 5, 1, 2, 7],
#     [3, 2, 1, 5, 4, 6, 7],
#
# ]

# clusterization(rankings, 3)
