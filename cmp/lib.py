import math

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


# def deviation_sum(old_ranking, new_ranking):
#     return sum([(old - new) ** 2 for old, new in zip(old_ranking, new_ranking)])
