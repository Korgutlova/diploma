import functools
import itertools

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from cmp.lib import cmp, fill_inputs, put_best
from cmp.models import Weights


def base_page(request):
    pattern = [["Пост", 0], ["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]]
    patriotism = [["Пост", 0], ["грам/дип", 0], ["уч", 0]]
    all_criteria = [{'Культура': pattern}, {"Спорт": pattern}, {"Патриотизм": patriotism},
                    {"Публикации": [["У1", 0], ["У2", 0]],
                     "Школьный": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
                     "Муниципальный": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
                     "Региональный": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
                     "Всероссийский": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
                     "Общие": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
                     "Конференции": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
                     "Похвальные грамоты/письма": [["парам", 0]]},
                    {"Общественная": pattern}
                    ]
    old_ranking = []
    new_ranking = []
    difference = []
    name_groups = []
    func = lambda x: float("{0:.3f}".format(x))
    if request.method == "POST":
        weights = []
        for i in range(45):
            weights.append(int(request.POST[str(i)][0]))
        old_ranking, new_ranking, difference, name_groups = cmp(weights)
        put_best(weights, sum(difference))
        print("old", old_ranking)
        print("new", new_ranking)
        print("diff", difference)
        all_criteria = fill_inputs(weights)
    new_ranking = map(func, new_ranking)
    difference = map(func, difference)
    return render(request, 'cmp/base.html',
                  {"all_criteria": all_criteria, 'counter_id': functools.partial(next, itertools.count()),
                   'counter_name': functools.partial(next, itertools.count()),
                   'ranking': zip(old_ranking, new_ranking, difference, name_groups)})


def best_weights(request):
    best_weights = Weights.objects.all().order_by('deviations_sum')
    result = [[b_w.weights.split(), float("{0:.3f}".format(b_w.deviations_sum)), b_w.id] for b_w in best_weights]
    return render(request, 'cmp/best_weights.html', {'best_weights': result})


def load_data(request, id):
    weights = list(map(int, Weights.objects.get(id=id).weights.split()))
    result, all_criteria = cmp(weights), fill_inputs(weights)
    func = lambda x: float("{0:.3f}".format(x))
    return render(request, 'cmp/base.html',
                  {"all_criteria": all_criteria, 'counter_id': functools.partial(next, itertools.count()),
                   'counter_name': functools.partial(next, itertools.count()),
                   'ranking': zip(result[0], map(func, result[1]), map(func, result[2]), result[3])})


def groups(request):
    return render(request, 'cmp/groups.html', {})


def calc(request):
    b_w = Weights.objects.filter(type=request.GET['param']).order_by('deviations_sum').first()
    result = cmp(list(map(int, b_w.weights.split())), request.GET['param'])
    func = lambda x: float("{0:.3f}".format(x))
    ranking = zip(result[0], map(func, result[1]), map(func, result[2]), result[3])
    data = {'ranking': render_to_string('cmp/result_table.html', {'ranking': ranking})}
    return JsonResponse(data)
