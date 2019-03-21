import math
from itertools import permutations

import cexprtk
import django
import os

import numpy as np

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dipl.settings")
django.setup()

from py_expression_eval import Parser

from fls.models import CriterionValue, ParamValue

parser = Parser()


# типовая
def func1(a, b):
    return float(math.log(a, 2)) / (b + 53)


def parse_formula(formula, params_values):
    vars_func = parser.parse(formula).variables()
    vars = list(filter(lambda x: x.find('_') != -1, vars_func))
    funcs = list(filter(lambda x: x.find('_') == -1, vars_func))
    variables = {}
    for var in vars:
        variables[var] = params_values[int(var.split('_')[1])]
    st = cexprtk.Symbol_Table(variables)
    for func in funcs:
        st.functions[func] = globals()[func]
    calc_exp = cexprtk.Expression(formula, st)
    print(calc_exp())
    return calc_exp()


def calc_criterion_value(criterion, group):
    params = criterion.competition.competition_params
    param_values = []
    for param in params:
        param_values.append(ParamValue.objects.get(param=param, group=group).value)
    value = parse_formula(criterion.formula, param_values)
    CriterionValue.objects.create(criterion=criterion, group=group, value=value)


# parse_formula("5*a_0 + func1(a_1, a_2)/log(a_3)", [2, 8, 7, 5])

def median_kemeni(rankings):
    perms = list(permutations(range(1, len(rankings[0]) + 1)))
    dist_sums = []
    for perm in perms:
        sum = 0
        for ranking in rankings:
            sum += dist_kemeni(perm, ranking)
        dist_sums.append(sum)

    return perms[dist_sums.index(min(dist_sums))]


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
                matrix[j, i] = 0
            elif ranking[i] == ranking[j]:
                matrix[i, j] = 1
            else:
                matrix[i, j] = 0
                matrix[j, i] = 1
    return matrix


# print(dist_kemeni([3, 4, 2, 1], [1, 2, 4, 3]))

# print(median_kemeni([[1, 3, 2], [2, 1, 3], [3, 1, 2]]))
