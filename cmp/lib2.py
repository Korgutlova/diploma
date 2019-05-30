import pickle
import random

from openpyxl import load_workbook

file = './data.xlsx'

wb = load_workbook(filename=file, data_only=True)

ws = wb.get_sheet_by_name('Входные данные')

academic_performance = [cell[0].value for cell in ws['C2':'C16']]

input_file_template = './static/cmp_results/%s'

criteria = {
    'culture': (0, 5),
    'sport': (5, 10),
    'patriotism': (10, 13),
    'science': (13, 40),
    'social_work': (40, 45)
}


def save_data(param='kfavg'):
    file = open(input_file_template % param, 'wb')
    param_values = []
    if param == 'kfavg':
        ws = wb.get_sheet_by_name('Входные данные')
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
    jury_results = [cell[0].value for cell in ws['B2':'B16']]
    pickle.dump([param_values, name_groups, jury_results, academic_performance], file)


def calculate_estimations(data, weights):
    estimations = []

    culture = []
    sport = []
    science = []
    social_work = []
    patriotism = []

    for request_param_values in data:
        culture.append(sum([sc * w for sc, w in zip(request_param_values[:5], weights[:5])]))
        sport.append(sum([sc * w for sc, w in zip(request_param_values[5:10], weights[5:10])]))
        patriotism.append(sum([sc * w for sc, w in zip(request_param_values[10:13], weights[10:13])]))
        science.append(sum([sc * w for sc, w in zip(request_param_values[13:40], weights[13:40])]))
        social_work.append(sum([sc * w for sc, w in zip(request_param_values[40:45], weights[40:45])]))
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
        estimations.append(culture_norm + sport_norm + science_norm + social_norm + patriotism_norm +
                           academic_performance[
                               i])
    return estimations


def smart_gen():
    const_act = [0, 5, 10, 39, 40]
    d1_part = [(1, 4), (6, 9), (11, 12), (13, 14), (35, 38), (41, 44)]
    olimp = [(15, 18, 5), (19, 22, 6), (23, 26, 7), (27, 30, 8), (31, 34, 4)]
    coef = {}
    for ind in const_act:
        coef[ind] = random.randint(1, 9)
    for ind_st, ind_end in d1_part:
        ind = ind_end
        est = random.randint(4, 9)
        while ind >= ind_st:
            coef[ind] = est
            ind -= 1
            est -= 1
    for ind_st, ind_end, est_st in olimp:
        ind = ind_end
        est = est_st
        while ind >= ind_st:
            coef[ind] = est
            ind -= 1
            est -= 1
    coef = dict(sorted(coef.items(), key=lambda item: item[0]))
    return list(coef.values())


def save_ests_all_params():
    for param in ['kfavg', 'avg', 'count']:
        save_data(param=param)
