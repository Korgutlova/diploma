import functools
import itertools

from django.shortcuts import render

from cmp.lib import cmp


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
    if request.method == "POST":
        weights = []
        for i in range(45):
            weights.append(int(request.POST[str(i)][0]))
        old_ranking, new_ranking, difference = cmp(weights)
        print(old_ranking)
        print(new_ranking)
        print(difference)

    return render(request, 'cmp/base.html',
                  {"all_criteria": all_criteria, 'counter_id': functools.partial(next, itertools.count()),
                   'counter_name': functools.partial(next, itertools.count()), 'new_ranking': new_ranking,
                   'old_ranking': old_ranking, 'difference': difference})


def calculate(request):
    n = 20
    for a in range(n):
        print(a)
    # return Redirect(reverse("cmp:base", kwargs={}))

    return render(request, 'cmp/base.html', {})
