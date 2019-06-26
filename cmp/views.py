import functools
import itertools
import pickle

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from cmp.lib import cmp

input_file_template = './static/cmp_results/2weights-%s'


def cmp_estimations(request):
    return render(request, 'cmp/request_estimations.html', {})


def calculate_estimations_difference(request):
    file = open(input_file_template % request.GET['param'], 'rb')
    best_weights = pickle.load(file)
    request_estimations = cmp(list(map(int, best_weights.split())), request.GET['param'])
    func = lambda x: float("{0:.3f}".format(x))
    estimations = zip(request_estimations[0], map(func, request_estimations[1]), map(func, request_estimations[2]),
                      request_estimations[3])
    data = {'ranking': render_to_string('cmp/table.html', {'estimations': estimations})}
    return JsonResponse(data)
