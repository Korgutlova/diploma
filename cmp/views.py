import functools
import itertools

from django.shortcuts import render

from cmp.lib import cmp, fill_inputs


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
