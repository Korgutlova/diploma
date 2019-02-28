import math
import cexprtk

from py_expression_eval import Parser

parser = Parser()

#типовая
def func1(a, b):
    return float(math.log(a, 2)) + b


def parse_formula(formula):
    vars_func = parser.parse(formula).variables()
    vars = list(filter(lambda x: x.find('_') != -1, vars_func))
    funcs = list(filter(lambda x: x.find('_') == -1, vars_func))
    variables = {}
    for var in vars:
        variables[var] = 5
    st = cexprtk.Symbol_Table(variables)
    for func in funcs:
        st.functions[func] = globals()[func]
    calc_exp = cexprtk.Expression(formula, st)
    print(calc_exp())


parse_formula("5*a_1 + func1(a_2, a_3)/log(a_4)")
