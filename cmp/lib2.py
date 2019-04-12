import copy
import pickle

import numpy as np
from openpyxl import load_workbook

file = '../data.xlsx'

wb = load_workbook(filename=file, data_only=True)

ws = wb.get_sheet_by_name('Входные данные')

name_groups = [cell[0].value for cell in ws['A2':'A16']]
old_ranking = [cell[0].value for cell in ws['B2':'B16']]
academic_performance = [cell[0].value for cell in ws['C2':'C16']]

input_file_template = '../static/result/%s'


def save_data(param='kfavg'):
    file = open(input_file_template % param, 'wb')
    param_values = []
    if param == 'kfavg':
        ws = wb.get_sheet_by_name('Входные данные')
        param_values = [list(map(lambda x: x.value, row)) for row in ws['D2':'AV16']]
    elif param == 'kf':
        ws = wb.get_sheet_by_name('Входные данные (кф)')
        param_values = [list(map(lambda x: x.value, row)) for row in ws['D2':'AV16']]

    elif param == 'avg' or param == 'c':
        ws = wb.get_sheet_by_name('Входные данные (кол)')
        param_values = [list(map(lambda x: x.value, row)) for row in ws['D2':'AV16']]
        if param == 'avg':
            counts = [cell[0].value for cell in ws['AW2':'AW16']]
            for i in range(len(param_values)):
                for j in range(len(param_values[i])):
                    param_values[i][j] = param_values[i][j] / counts[i]

    ws = wb.get_sheet_by_name('Входные данные')
    name_groups = [cell[0].value for cell in ws['A2':'A16']]
    old_ranking = [cell[0].value for cell in ws['B2':'B16']]
    academic_performance = [cell[0].value for cell in ws['C2':'C16']]

    pickle.dump([param_values, name_groups, old_ranking, academic_performance], file)


def save_ests_all_params():
    for param in ['kfavg', 'kf', 'c', 'avg']:
        save_data(param=param)


def calculate_est(data, weights):
    new_ranking = []

    culture = []
    sport = []
    science = []
    social_work = []
    patriotism = []

    for group in data:
        culture.append(sum([sc * w for sc, w in zip(group[:5], weights[:5])]))
        sport.append(sum([sc * w for sc, w in zip(group[5:10], weights[5:10])]))
        patriotism.append(sum([sc * w for sc, w in zip(group[10:13], weights[10:13])]))
        science.append(sum([sc * w for sc, w in zip(group[13:40], weights[13:40])]))
        social_work.append(sum([sc * w for sc, w in zip(group[40:45], weights[40:45])]))
    max_culture, min_culture = max(culture), min(culture)
    max_sport, min_sport = max(sport), min(sport)
    max_science, min_science = max(science), min(science)
    max_social_work, min_social_work = max(social_work), min(social_work)
    max_patriotism, min_patriotism = max(patriotism), min(patriotism)
    for i in range(len(data)):
        culture_norm = (culture[i] - min_culture) / (max_culture - min_culture) * 10
        sport_norm = (sport[i] - min_sport) / (max_sport - min_sport) * 10
        science_norm = (science[i] - min_science) / (max_science - min_science) * 10
        social_norm = (social_work[i] - min_social_work) / (max_social_work - min_social_work) * 10
        patriotism_norm = (patriotism[i] - min_patriotism) / (max_patriotism - min_patriotism) * 10
        new_ranking.append(culture_norm + sport_norm + science_norm + social_norm + patriotism_norm +
                           academic_performance[
                               i])
    return new_ranking

pattern = [["Пост", 0], ["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]]
olimp_pattern = [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]]
patriotism_ = [["Пост", 0], ["грам/дип", 0], ["уч", 0]]
science = {"Публикации": [["У1", 0], ["У2", 0]],
           "Школьный": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
           "Муниципальный": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
           "Региональный": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
           "Всероссийский": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
           "Общие": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
           "Конференции": [["Д1", 0], ["Д2", 0], ["Д3", 0], ["уч", 0]],
           "Похвальные грамоты/письма": [["парам", 0]]}


def fill_inputs(weights):
    culture, social_work, sport, patriotism = np.array(copy.deepcopy(pattern)), np.array(
        copy.deepcopy(pattern)), np.array(
        copy.deepcopy(pattern)), np.array(copy.deepcopy(patriotism_))
    culture[:, 1], sport[:, 1], social_work[:, 1], patriotism[:, 1] = weights[:5], weights[5:10], weights[
                                                                                                  40:45], weights[10:13]
    articles = np.array(copy.deepcopy(science["Публикации"]))
    articles[:, 1] = weights[13:15]
    olymp_conf = {}
    c = 15
    for key in list(science.keys())[1:-1]:
        olymp_conf[key] = np.array(copy.deepcopy(olimp_pattern))
        olymp_conf[key][:, 1] = weights[c:c + 4]
        olymp_conf[key] = olymp_conf[key].tolist()
        c += 4
    certs = copy.deepcopy(science["Похвальные грамоты/письма"])
    certs[0][1] = weights[39]
    science_ = {}
    science_["Публикации"] = articles.tolist()
    science_ = {**science_, **olymp_conf}
    science_["Похвальные грамоты/письма"] = certs

    all_criteria = [{'Культура': culture.tolist()}, {"Спорт": sport.tolist()}, {"Патриотизм": patriotism.tolist()},
                    science_,
                    {"Общественная": social_work.tolist()}
                    ]

    return all_criteria

# def generate_random_group_weights(iter_count, group_number, param):
#     random_weights = [[randint(1, 9) for i in range(45)] for i in range(iter_count)]
#     min = sum(cmp(random_weights[0], param=param, group=group_number)[2])
#     best_weights = random_weights[0]
#     random_weights.pop(0)
#     for weights in random_weights:
#         result = sum(cmp(weights, param=param, group=group_number)[2])
#         if result < min:
#             min = result
#             best_weights = weights
#     GroupWeights.objects.create(group_name=name_groups[group_number], weights=' '.join(str(e) for e in best_weights),
#                                 deviations_sum=min, type=param)
#
#
# def groups(iter_count):
#     for param in ['c', 'avg']:
#         for j in range(len(name_groups)):
#             generate_random_group_weights(iter_count, j, param)
#
#
# def each_group_separately(param):
#     input_file = open(input_file_template % param, 'rb')
#     data = pickle.load(input_file)[0]
#     cmp = []
#     func = lambda x: float("{0:.3f}".format(x))
#     for i in range(len(name_groups)):
#         group_weights = list(map(int, GroupWeights.objects.get(group_name=name_groups[i], type=param).weights.split()))
#         new_value = sum([sc * w for sc, w in zip(group_weights, data[i])])
#         old_value = old_ranking[i]
#         diff = abs(new_value - old_value)
#         cmp.append([old_value, func(new_value), func(diff), name_groups[i]])
#     return cmp

