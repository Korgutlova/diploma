import math
import cexprtk
import django
import os
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
    print(vars)
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


parse_formula("5*a_0 + func1(a_1, a_2)/log(a_3)", [2, 8, 7, 5])
