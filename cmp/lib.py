import copy
import math

import numpy as np
from openpyxl import load_workbook

file = './data.xlsx'

wb = load_workbook(filename=file, data_only=True)

ws = wb.get_sheet_by_name('Входные данные')

data = [list(map(lambda x: x.value, row)) for row in ws['D2':'AV16']]

name_groups = [cell[0].value for cell in ws['A2':'A16']]
old_ranking = [cell[0].value for cell in ws['B2':'B16']]
academic_performance = [cell[0].value for cell in ws['C2':'C16']]


def cmp(weights):
    new_ranking = []

    culture = []
    sport = []
    science = []
    social_work = []
    patriotism = []

    culture_norm = []
    sport_norm = []
    science_norm = []
    social_norm = []
    patriotism_norm = []

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
        culture_norm.append((culture[i] - min_culture) / (max_culture - min_culture) * 10)
        sport_norm.append((sport[i] - min_sport) / (max_sport - min_sport) * 10)
        science_norm.append((science[i] - min_science) / (max_science - min_science) * 10)
        social_norm.append((social_work[i] - min_social_work) / (max_social_work - min_social_work) * 10)
        patriotism_norm.append((patriotism[i] - min_patriotism) / (max_patriotism - min_patriotism) * 10)
    for i in range(len(data)):
        new_ranking.append(
            culture_norm[i] + sport_norm[i] + science_norm[i] + social_norm[i] + patriotism_norm[i] +
            academic_performance[
                i])
    return old_ranking, new_ranking, [abs(old - new) for old, new in zip(old_ranking, new_ranking)], name_groups


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


# def deviation_sum(old_ranking, new_ranking):
#     return sum([(old - new) ** 2 for old, new in zip(old_ranking, new_ranking)])
